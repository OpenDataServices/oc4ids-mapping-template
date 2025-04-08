import click
import csv
import json
import jsonref
import re
import subprocess
import requests
import xlsxwriter
import yaml

from io import StringIO
from ocdskit.schema import get_schema_fields

# Note to include before additional fields section of each (OC4IDS) mapping sheet
ADDITIONAL_FIELDS_NOTE = {
    "en": "Data which does not map to the OC4IDS schema can be included in your OC4IDS publication using additional fields. List your additional fields below and open an issue on the OC4IDS Github so that they can be considered for inclusion in a future version of the standard: https://github.com/open-contracting/infrastructure. Include the proposed field path, type, title, description and an example of the data provided in the field.",
    "es": "Los datos que no se puedan mapear al esquema OC4IDS pueden incluirse en su publicación OC4IDS utilizando camposa adicionales. Enliste sus campos adicionales más bajo y abra un issue en el Github de OC4IDS para que puedan considerarse para su inclusión en una versión futura del estándar:https://github.com/open-contracting/infrastructure. Incluya la ruta de campo propuesta, tipo, título, descripción y un ejemplo de los datos que se proveen en el campo. "
}

# Regular expression to find links in schema descriptions
INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def get(url):
    """
    GETs a URL and returns the response. Raises an exception if the status code is not successful.
    """
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response


def csv_reader(url):
    """
    Read a CSV from a URL and returns a ``csv.Reader`` object.
    """
    return csv.reader(StringIO(get(url).text))


@click.group()
def cli():
    pass


@cli.command()
@click.option('-v',
              '--version',
              default='latest',
              show_default=True,
              help = "The OC4IDS version or branch from which to generate the template."
              )
@click.option('-s',
              '--staging',
              is_flag=True,
              show_default=True,
              default=False,
              help="Whether to fetch the OC4IDS schema and CoST IDS mapping from the staging server. Set to true when specifying a development branch in --version")
@click.option('-l',
              '--language',
              default='en',
              show_default=True,
              type=click.Choice(["en", "es"], case_sensitive=False),
              help = "The language in which to generate the template."
              )
@click.option('-c',
              '--compatibility',
              default='excel',
              show_default=True,
              type=click.Choice(["excel", "gsheets"], case_sensitive=False),
              help="The target application for the template.")
def create_template(version, staging, language, compatibility):
    """
    Create an XLSX template.
    """

    def write_mapping_row(sheet, row, field, title, description, field_type):
        """
        Write a row representing a field to a mapping sheet.
        """
        
        if field.schema['type'] in ('object', 'array'):
            if field.required:
                cell_format = formats["object_array_required"]
            else:
                cell_format = formats["object_array"]
            sheet["worksheet"].write_row(row, 0, [f"`{field.path}`", str(field_type), title], cell_format)
            sheet["worksheet"].merge_range(row, 3, row, 5, description, cell_format)
        else:
            if field.required:
                cell_format = formats["field_required"]
            else:
                cell_format = formats["field"]
            sheet["worksheet"].write_row(row, 0, [f"`{field.path}`", str(field_type), title, description], cell_format)
            sheet["worksheet"].write(row, 4, None, formats["input"])
            sheet["worksheet"].data_validation(
                row, 4, row, 4, {"validate": "list", "source": f"='{sheets['elements']['title'][language]}'!$A$5:$A$500"})
            sheet["worksheet"].write_formula(
                row, 5, f"=IFERROR(VLOOKUP(E{row + 1},'{sheets['elements']['title'][language]}'!$A:$E,5,FALSE),"")", formats["calculated"])

        sheet["worksheet"].write(row, 6, None, formats["input"])
        formula = f"""=IFERROR(TEXTJOIN("\n",TRUE,FILTER('{sheets['ids']['title'][language]}'!$H$4:$H$200,(NOT(ISERROR(SEARCH(A{row+1},'{sheets['ids']['title'][language]}'!$F$4:$F$200))))*('{sheets['ids']['title'][language]}'!$G$4:$G$200="Yes"))),"")"""
        sheet["worksheet"].write_formula(row, 7, formula, formats["calculated"])

    readme_url = {
        "en": "https://github.com/OpenDataServices/oc4ids-mapping-template/blob/main/README.md",
        "es": "https://github.com/OpenDataServices/oc4ids-mapping-template/blob/main/README.md"
    }
    
    # Load sheet configuration
    with open("config/sheets.json") as f:
        sheets = json.load(f)
    
    # Load column configuration for mapping sheets
    with open("config/mapping_columns.json") as f:
        mapping_columns = json.load(f)

    for sheet in sheets.values():
        # Set row counts
        sheet["row_count"] = 0

        # Set columns for mapping sheets
        if sheet.get("type") == "mapping":
            sheet["columns"] = mapping_columns

    # Get dereferenced schema
    base_url = f"https://standard.open-contracting.org/{'staging/' if staging else ''}/infrastructure/{version}/{language}"
    schema_url = f"{base_url}/project-schema.json"
    schema = get(schema_url).json()
    schema = jsonref.JsonRef.replace_refs(schema, base_uri=schema_url)

    # Remove links from top-level schema description
    links = dict(INLINE_LINK_RE.findall(schema['description']))
    for key, link in links.items():
        schema['description'] = schema['description'].replace('[' + key + '](' + link + ')', key)

    # Create workbook
    workbook_filename = f"oc4ids_mapping_template_{language}_{compatibility}.xlsx"
    workbook = xlsxwriter.Workbook(workbook_filename, {'use_future_functions': True})

    # Add cell formats
    formats = {
        "title": workbook.add_format({"font_size": 14}),
        "subtitle": workbook.add_format({"italic": True, "text_wrap": True}),
        "headers": workbook.add_format({"bold": True, "text_wrap": True, "border": 7}),
        "example": workbook.add_format({"italic": True, "text_wrap": True, "bg_color": "#f3f3f3", "border": 7}),
        "input": workbook.add_format({"text_wrap": True, "bg_color": "#fff2cc", "border": 7, "locked": False}),
        "calculated": workbook.add_format({"text_wrap": True, "bg_color": "#d9ead3", "border": 7}),
        "ids_element": workbook.add_format({"text_wrap": True, "border": 7}),
        "object_array": workbook.add_format({"bg_color": "#efefef", "text_wrap": True, "border": 7}),
        "object_array_required": workbook.add_format({"bg_color": "#efefef", "font_color": "red", "text_wrap": True, "border": 7}),
        "field": workbook.add_format({"text_wrap": True, "border": 7}),
        "field_required": workbook.add_format({"font_color": "red", "text_wrap": True, "border": 7})
    }
    for format in formats.values():
        format.set_align("top")

    for slug, sheet in sheets.items():
        # Add worksheet
        worksheet = workbook.add_worksheet(sheet["title"][language])
        worksheet.outline_settings(symbols_below=False)
        worksheet.set_default_row(hide_unused_rows=True)
        worksheet.protect()
        sheet["worksheet"] = worksheet

        # Set column widths
        for col, width in enumerate([col["width"] for col in sheet["columns"]]):
            worksheet.set_column_pixels(col, col, width)
        
        # Hide empty columns
        for col in range(len(sheet["columns"]), 26):
          worksheet.set_column(col, col, None, None, {"hidden": True})

        # Add title and subtitle
        worksheet.merge_range(0, 0, 0, len(sheet["columns"]) - 1, sheet["title"][language], formats["title"])
        sheet["row_count"] += 1
        if "subtitle" in sheet:
          worksheet.merge_range(sheet["row_count"], 0, sheet["row_count"], len(sheet["columns"]) - 1, sheet["subtitle"][language], formats["subtitle"])
          if slug == "readme":
              worksheet.write_url(sheet["row_count"], 0, readme_url[language], None, sheet["subtitle"][language])
          sheet["row_count"] += 1

        # Add column headers and freeze rows
        headers = [col["header"][language] for col in sheet["columns"] if "header" in col]
        notes = [col["note"][language] for col in sheet["columns"] if "note" in col]
        if len(headers) > 0:
            worksheet.write_row(sheet["row_count"], 0, headers, formats["headers"])
            for col, note in enumerate(notes):
                worksheet.write_comment(sheet["row_count"], col, note)
            sheet["row_count"] += 1
            worksheet.freeze_panes(sheet["row_count"], 0)            

        # Add examples
        examples = [col["example"][language] for col in sheet["columns"] if "example" in col]            
        if len(examples) > 0:
            worksheet.write_row(sheet["row_count"], 0, examples, formats["example"])
            sheet["row_count"] += 1

        # Add columns to (Source) 1. Systems sheet
        if slug == "sources":
            for col in range(len(sheet["columns"])):
                worksheet.write_column(sheet["row_count"], col, [None for i in range(25)], formats["input"])

        # Add columns to (Source) 2. Fields sheet
        elif slug == "elements":
            worksheet.write_column(sheet["row_count"], 0, [f'=TEXTJOIN(".", TRUE, B{sheet["row_count"] + i}:D{sheet["row_count"] + i})' for i in range(1, 201)], formats["calculated"])
            
            for col in range (1, 8):
                worksheet.write_column(sheet["row_count"], col, [None for i in range(200)], formats["input"])
            
            lookup_formulae = [
                (f"""=IFERROR(TEXTJOIN(
                  "\n",
                  TRUE, 
                  IFERROR(FILTER('{sheets["projects"]["title"][language]}'!$A$1:$A$1000,'{sheets["projects"]["title"][language]}'!$E$1:$E$1000=$A{sheet["row_count"]+i}),""),
                  IFERROR(FILTER('{sheets["contracts"]["title"][language]}'!$A$1:$A$1000,'{sheets["contracts"]["title"][language]}'!$E$1:$E$1000=$A{sheet["row_count"]+i}),""),
                  IFERROR(FILTER('{sheets["releases"]["title"][language]}'!$A$1:$A$1000,'{sheets["releases"]["title"][language]}'!$E$1:$E$1000=$A{sheet["row_count"]+i}),""),
                  IFERROR(FILTER('{sheets["parties"]["title"][language]}'!$A$1:$A$1000,'{sheets["parties"]["title"][language]}'!$E$1:$E$1000=$A{sheet["row_count"]+i}),"")),
                  "")""") for i in range(1,201)]
            
            worksheet.write_column(sheet["row_count"], 8, lookup_formulae, formats["calculated"])
            
            worksheet.data_validation(sheet["row_count"], 1, sheet["row_count"] + 200, 1, {"validate": "list",
                                      "source": f"='{sheets['sources']['title'][language]}'!$A$5:$A$29"})
            worksheet.data_validation(sheet["row_count"], 6, sheet["row_count"] + 200, 6, {"validate": "list", "source": [
                                      "string", "integer", "date", "date-time", "codelist", "other"]})

        # Add rows to (CoST) IDS Elements sheet
        elif slug == "ids":

            # Write core elements
            mapping_csvs = [
                "project-level-identification.csv",
                "project-level-preparation.csv",
                "reactive-project-level-identification-preparation.csv",
                "project-level-completion.csv",
                "reactive-project-level-completion.csv",
                "process-level-procurement.csv",
                "reactive-process-level-procurement.csv",
                "reactive-process-level-contract.csv",
                "process-level-implementation.csv",
                "reactive-process-level-implementation.csv"
            ]
            for filename in mapping_csvs:
                mapping_name = filename.split(".")[0].split("-")
                mapping_type = "reactive" if "reactive" in mapping_name else "proactive"
                mapping_level = "project" if "project" in mapping_name else "process"
                mapping_stage = mapping_name[-1]

                reader = csv_reader(f"{base_url}/{filename}")
                next(reader, None)

                for element in reader:
                    worksheet.write_row(sheet["row_count"],
                                        0,
                                        [
                                            f"Core - {mapping_type}",
                                            mapping_level,
                                            mapping_stage,
                                            element[0],
                                            element[1],
                                            "\n".join([f"`{path}`" for path in element[4].split(",")]),
                                            "",
                                            f"{element[0]} (Core - {mapping_type}: {mapping_level} {mapping_stage})"
                                        ],
                                        formats["ids_element"])
                    worksheet.write(sheet["row_count"], 6, "Yes", formats["input"])
                    worksheet.data_validation(sheet["row_count"], 6, sheet["row_count"], 6, {"validate": "list", "source": ["Yes", "No"]})
                    sheet["row_count"] += 1

            # Write sustainability elements
            response = get(f"{base_url}/sustainability.yaml")
            content = response.content.decode(response.encoding)
            sustainability_mapping = yaml.safe_load(content)

            for element in sustainability_mapping:
                worksheet.write_row(sheet["row_count"],
                                    0,
                                    [
                                        f"Sustainability: {element['module']}",
                                        "",
                                        "",
                                        element["title"],
                                        element["disclosure format"],
                                        "\n".join([f"`{path[1:]}`" for path in element["fields"]]),
                                        "Yes",
                                        f"{element['title']} (Sustainability - {element['module']})"
                                    ],
                                    formats["ids_element"]
                                    )
                worksheet.write(sheet["row_count"], 6, "Yes", formats["input"])
                worksheet.data_validation(sheet["row_count"], 6, sheet["row_count"], 6, {"validate": "list", "source": ["Yes", "No"]})
                sheet["row_count"] += 1
            
            worksheet.set_column(6, 6, None, formats["input"])

    # The parties mapping sheet repeats the fields in the `parties` section for each organization reference
    org_refs = []
    parties_fields = []

    # Add each field in the schema to one of the mapping sheets
    for field in get_schema_fields(schema):

        # Skip the definitions section of the schema
        if field.definition_pointer_components:
            continue

        # Set the separator to use in field paths
        field.sep = '/'

        # Capture organization references
        if ((hasattr(field.schema, '__reference__') and (field.schema.__reference__['$ref'] == '#/definitions/OrganizationReference')) or
                ('items' in field.schema and 'title' in field.schema['items'] and (field.schema['items']['title'] in ['Organization reference', 'Referencia de la organización']))):
            org_refs.append(field)

        # Concatenate titles, descriptions and types for refs and arrays
        if hasattr(field.schema, '__reference__'):
            title = field.schema.__reference__['title'] + ' (' + field.schema['title'] + ')'
            description = field.schema.__reference__['description'] + ' (' + field.schema['description'] + ')'
            field_type = field.schema['type']

        elif 'items' in field.schema and 'properties' in field.schema['items'] and 'title' in field.schema['items']:
            title = field.schema['title'] + ' (' + field.schema['items']['title'] + ')'
            description = field.schema['description'] + ' (' + field.schema['items'].get('description', '') + ')'
            field_type = field.schema['type'] + ' (' + field.schema['items']['type'] + ')'

        else:
            title = field.schema['title']
            description = field.schema['description']
            field_type = field.schema['type']

        # Remove links from descriptions
        links = dict(INLINE_LINK_RE.findall(description))

        for key, link in links.items():
            description = description.replace('[' + key + '](' + link + ')', key)

        # Determine which mapping sheet to add the field to
        if 'contractingProcesses' in field.path and 'releases' in field.path:
            sheet = sheets["releases"]
        elif 'contractingProcesses' in field.path:
            sheet = sheets["contracts"]
        elif field.path == 'parties':
            sheet = sheets["parties"]
        elif 'parties' in field.path:
            parties_fields.append(field)  # Capture fields to repeat in parties sheet
        else:
            sheet = sheets["projects"]

        # Write row to mapping sheet, skip fields in the `parties` section
        if 'parties' not in field.path or field.path == 'parties':
            row = sheet["row_count"]
            write_mapping_row(sheet, row, field, title, description, field_type)
            sheet["row_count"] += 1

    # Write rows to the parties sheet, repeating fields from the `parties` section for each organization reference
    sheet = sheets["parties"]
    row = sheet["row_count"]

    # For organization references, use the title and description of the referencing field
    for field in org_refs:
        if hasattr(field.schema, '__reference__'):
            title = field.schema.__reference__['title']
            description = field.schema.__reference__['description']
        else:
            title = field.schema['title']
            description = field.schema['description']

        write_mapping_row(sheet, row, field, title, description, field.schema['type'])
        sheet["worksheet"].set_row(row, None, None, {'collapsed': True})
        row += 1

        for field in parties_fields:
            write_mapping_row(sheet, row, field, field.schema['title'],
                              field.schema['description'], field.schema['type'])
            sheet["worksheet"].set_row(row, None, None, {'level': 1, 'hidden': True})
            row += 1

    sheet["row_count"] = row

    for slug, sheet in sheets.items():
        
        if sheet.get("type") == "mapping":

            # Write additional fields rows to mapping sheets
            sheet["worksheet"].merge_range(sheet["row_count"], 0, sheet["row_count"], 6,
                                           ADDITIONAL_FIELDS_NOTE[language], formats["subtitle"])
            sheet["row_count"] += 1

            for i in range(4):
                sheet["worksheet"].write_row(sheet["row_count"], 0, ["" for i in range(7)], formats["input"])
                sheet["worksheet"].data_validation(sheet["row_count"], 4, sheet["row_count"], 4, {
                                                   "validate": "list", "source": f"='{sheets['elements']['title'][language]}'!$A$5:$A$500"})
                sheet["worksheet"].write_formula(
                    sheet["row_count"], 5, f"=IFERROR(VLOOKUP(G{sheet['row_count'] + 1},'{sheets['elements']['title'][language]}'!$A:$E,5,FALSE),"")", formats["calculated"])
                sheet["row_count"] += 1

            # Add filters
            sheet["worksheet"].autofilter(2, 0, sheet["row_count"], 7)

    workbook.close()

    # Remove _xlfn._xlws. prefix from FILTER formulae
    if compatibility == 'gsheets':
        subprocess.run("mkdir .tmp", shell=True)
        subprocess.run(f"unzip {workbook_filename} -d .tmp", shell=True)
        subprocess.run("find .tmp/xl/worksheets -type f -name '*.xml' -exec sed -i 's/_xlfn\._xlws\.//g' {} \;", shell=True)
        subprocess.run(f"zip -f -0 -r ../{workbook_filename} .", cwd=".tmp", shell=True)
        subprocess.run("rm -rf .tmp", shell=True)


if __name__ == '__main__':
    cli()

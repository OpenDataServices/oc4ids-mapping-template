#  Open Contracting for Infrastructure Data Standard (OC4IDS) Field-Level Mapping Template

Use this template to document your sources of infrastructure project data and to document how that data maps to OC4IDS - that is, identifying which [data elements](https://en.wikipedia.org/wiki/Data_element) within your data sources match which [OC4IDS fields](https://standard.open-contracting.org/infrastructure/latest/en/reference/schema/).

To learn more about OC4IDS, read its [documentation](https://standard.open-contracting.org/infrastructure/latest/en/).

> [!IMPORTANT]
> Trying to map your procurement data to the Open Contracting Data Standard (OCDS)? Use the [OCDS Field-Level Mapping Template](https://www.open-contracting.org/resources/ocds-field-level-mapping-template/) instead.

## Access the template

The template is available in the following versions and languages:

* Microsoft Excel (2010+) ([English](https://drive.google.com/uc?export=download&id=13mRFjRwBFuE8Sni0oDFsEG7VgqS0rpTO), [Spanish](https://drive.google.com/uc?export=download&id=1jsdlKmRoMPI4AZLDCdQcR8kjOrwU-1i7))
* Google Sheets ([English](https://docs.google.com/spreadsheets/d/1g_mrD8MmdPhdLde7yuBqIDTpD5SYWeJcv8R__S48gLY/), [Spanish](https://docs.google.com/spreadsheets/d/1WjqDEjkiEK4rBm0n2Ef4VndbwvSNsiZaNWTE5KOTEmI/copy))

## How to use the template

1. Use the `(Source) 1. Systems` sheet to list your sources of infrastructure project data.
1. Use the `(Source) 2. Fields` sheet to list all of the data elements within your data sources.
1. Optionally, use the `(CoST) IDS Elements` sheet to select the elements of the [CoST IDS](https://standard.open-contracting.org/infrastructure/latest/en/cost/) that you want to map.
1. Use the `(OC4IDS)` sheets to match OC4IDS fields to your data elements, to identify gaps in the data that you collect, and to identify data elements that do not match any fields or codes in OC4IDS.

To learn more about using the template, see the [OC4IDS Field-Level Mapping Template Tutorial](https://www.open-contracting.org/resources/oc4ids-field-level-mapping-template-tutorial/).

> [!TIP]
> Need help? The Open Contracting Partnership and CoST - the Infrastructure Transparency Initiative can provide [free-of-charge support](https://standard.open-contracting.org/infrastructure/latest/en/support/).

## Developer documentation

The template is generated from the OC4IDS schema and documentation using `manage.py create-template`.

> [!TIP]
> Not comfortable with using a local development environment? You can use the [Google Colab notebook]() to update the template for a new version of the OC4IDS schema.

### Set up your development environment

#### Clone the repository

```bash
git clone git@github.com:OpenDataServices/oc4ids-mapping-template.git
cd oc4ids-mapping-template
```

Subsequent instructions assume that your current working directory is `oc4ids-mapping-template`, unless otherwise stated.

#### Create and activate a Python virtual environment

The following instructions assume you have [Python 3.8](https://www.python.org/downloads/) or newer installed on your machine.

You can use either `pyenv` or `python3-venv` for this step.

##### pyenv

1. Install [pyenv](https://github.com/pyenv/pyenv). The [pyenv installer](https://github.com/pyenv/pyenv-installer) is recommended.
1. Create a virtual environment.

    ```bash
    pyenv virtualenv oc4ids-mapping-template
    ```

1. Activate the virtual environment.

    ```bash
    pyenv activate oc4ids-mapping-template
    ```

1. Set the local application-specific virtual environment. Once set, navigating to the `oc4ids-mapping-template` directory will automatically activate the environment.

    ```bash
    pyenv local oc4ids-mapping-template
    ```

##### virtualenv

1. Create a virtual environment named `.ve`.
  1. Linux/MacOS users:

      ```bash
      python3 -m venv .ve
      ```

  1. Windows users:

      ```bash
      py -m venv .ve
      ```

1. Activate the virtual environment. You must run this command for each new terminal session.
  1. Linux/MacOS users:

      ```bash
      source .ve/bin/activate
      ```

  1. Windows users:

      ```bash
      .\.ve\Scripts\activate
      ```  

#### Install requirements:

```bash
pip install -r requirements.txt
```

### Update the template for a new version of the OC4IDS schema

#### Excel

For each language:

1. Update the Excel template using the latest OC4IDS schema. For example, to update the English template:

```bash
python manage.py create-template -v latest -l en -c excel
```

1. Open the template in Excel or [Excel Online](https://www.microsoft.com/en-nz/microsoft-365/excel). In each sheet, select all cells (`Ctrl+A`) and auto fit row height.
1. Open the [field-level mapping template folder](https://drive.google.com/drive/folders/1JiIdzm7uyrBDLHHzn0LOff-tE5JN-pnh) and:
  1. Right-click on the current version of the template
  1. Select **File information > Manage versions**
  1. Upload the new version.

#### Google Sheets

For each language:

1. Update the Google Sheets template using the latest OC4IDS schema. For example, to update the English template:

```bash
python manage.py create-template -v latest -l en -c gsheets
```

2. Open the current version of the template ([English](https://docs.google.com/spreadsheets/d/1g_mrD8MmdPhdLde7yuBqIDTpD5SYWeJcv8R__S48gLY), [Spanish](https://docs.google.com/spreadsheets/d/1WjqDEjkiEK4rBm0n2Ef4VndbwvSNsiZaNWTE5KOTEmI)), go to **File > Import** and upload the updated version, choosing to replace the existing spreadsheet.

### Edit the template's structure, format or static content

Edit `config/sheets.json` or `config/mapping_columns.json` to update:

* Sheet titles
* Sheet subtitles
* Column widths
* Column headers
* Column notes
* Example values
* Translations

Mapping sheets (prefixed with `(OC4IDS`) have consistent columns, which are specified in `config/mapping_columns.json`.

If you edit string values in the config files, you must update the associated translations.

Edit `manage.py` to update:

* Cell formats
* Formulae
* Data validation
* Logic for determining which mapping sheet to add each field to

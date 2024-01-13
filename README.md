<p align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/5968/5968914.png" width="100" />
</p>
<p align="center">
    <h1 align="center">SFDC-TASK-IMPORT</h1>
</p>
<p align="center">
    <em><code>Exchange to Salesforce event exporter: Simplify data integration with a single Python script</code></em>
</p>
<p align="center">
	<img src="https://img.shields.io/github/license/mguyard/SFDC-Task-Import?style=default&color=0080ff" alt="license">
	<img src="https://img.shields.io/github/last-commit/mguyard/SFDC-Task-Import?style=default&color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/mguyard/SFDC-Task-Import?style=default&color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/mguyard/SFDC-Task-Import?style=default&color=0080ff" alt="repo-language-count">
<p>
<p align="center">
	<!-- default option, no dependency badges. -->
</p>
<hr>

## 🔗 Quick Links

> - [📍 Overview](#-overview)
> - [📦 Features](#-features)
> - [📂 Repository Structure](#-repository-structure)
> - [🚀 Getting Started](#-getting-started)
>   - [⚙️ Installation](#️-installation)
>   - [🤖 Running SFDC-Task-Import](#-running-SFDC-Task-Import)
>   - [🧩 Parameters](#-parameters)
> - [🤝 Contributing](#-contributing)
> - [📄 License](#-license)

---

## 📍 Overview

### Objective

This Python script has been developed to facilitate the export of events from Microsoft Exchange into a Salesforce-compatible CSV format. It provides an automated solution for retrieving event data from an Exchange API, validating it against a specified date range, filtering it according to defined criteria, and exporting it as a CSV file ready for import into Salesforce.

> [!IMPORTANT]
>
> This project is under development and meets certain criteria specific to my company. I encourage you to take a look at this project and adapt it to your needs if necessary.

### Motivation

The genesis of this script came from the need to simplify and optimize the tedious process of manually entering activities into Salesforce. Faced with the repetitive task of exporting events from Microsoft Exchange to Salesforce, I felt a compelling need to create an automated tool.

The aim was to put an end to the tedious manual entry of event data, providing an efficient solution for quickly and accurately integrating this crucial information into Salesforce. The script not only saves time by automating the process, but also reduces the risk of errors associated with manual data entry, improving data accuracy and consistency.

In short, this script has been designed to free users from the laborious burden of manual data entry, equipping them with a powerful tool that simplifies the integration of event data into Salesforce in an efficient and reliable way.

---

## 📦 Features

- Retrieve events from the Exchange API.
- Validate event timing according to the specified date range.
- Event filtering based on associated categories.
- Generate a CSV file suitable for import into Salesforce.

This script is designed to be flexible and customizable, offering command-line options for defining various parameters such as date range, maximum number of hours per day, and so on. It aims to simplify the process of integrating event data into Salesforce, providing an efficient tool for users working with both platforms.

---

## 📂 Repository Structure

```sh
└── SFDC-Task-Import/
    ├── .github
    │   └── workflows
    │       ├── build.yaml
    │       └── lint.yaml
    ├── Dockerfile
    ├── import-sfdc-task.py
    └── requirements.txt
```

---

## 🚀 Getting Started

***Requirements***

Ensure that the following dependencies are installed on your system :
- **[Docker Desktop](https://www.docker.com/products/docker-desktop)**: `Minimal version 4.26.1`

### ⚙️ Installation

> [!IMPORTANT]
>
> This script relies on the [jcalapi](https://github.com/pschmitt/jcalapi) library, which serves as a crucial component for converting Exchange calendars into an API for seamless interaction. As part of the installation process outlined below, this dependency will be automatically deployed alongside the main script.

```sh
docker create \
--name ExchangeAPI --restart unless-stopped \
-p 7042:7042 \
-e "EXCHANGE_EMAIL=<MyExchageEmailHere>" \
-e "EXCHANGE_USERNAME=<MyExchageUsernameHere>" \
-e "EXCHANGE_PASSWORD=<MyExchangePasswordHere>" \
pschmitt/jcalapi:latest
docker start ExchangeAPI
```

You can also add another environment variable named PAST_DAYS_IMPORT who can include an integer which is the number of days in past to include by default.

```sh
docker create \
--name ExchangeAPI --restart unless-stopped \
-p 7042:7042 \
-e "EXCHANGE_EMAIL=<MyExchageEmailHere>" \
-e "EXCHANGE_USERNAME=<MyExchageUsernameHere>" \
-e "EXCHANGE_PASSWORD=<MyExchangePasswordHere>" \
-e "PAST_DAYS_IMPORT=15"
pschmitt/jcalapi:latest
docker start ExchangeAPI
```

The main functionality of this script is encapsulated within a Docker container, providing a self-contained and reproducible environment. When you are ready to export events, you will launch this Docker container to execute the script.

### 🤖 Running SFDC-Task-Import

Use the following command to run SFDC-Task-Import:

```sh
docker run -it --rm \
--name SFDC-Task-Export \
-v "$(pwd)":/export \
ghcr.io/mguyard/import-sfdc-task:latest [PARAMETERS]
```

Example :

```sh
docker run -it --rm \
--name SFDC-Task-Export \
-v "$(pwd)":/export \
ghcr.io/mguyard/import-sfdc-task:latest \
--sfdc-user-id XXXXXXXXXXXX \
--output /export/myexportfile.csv
```

### 🧩 Parameters

| Flag (Long/Short)             | Default | Description                                                                                         | Type    | Status      |
|-----------------------|-------------------|-----------------------------------------------------------------------------------------------------|---------|-------------|
| `--api-url`/`-u`           | `http://host.docker.internal:7042` | URL de l'API JCALAPI                                                                               | String  | Optionnel    |
| `--sfdc-user-id`/`-i`      | -                 | Salesforce ID de l'utilisateur                                                                    | String  | Obligatoire |
| `--last-week`         | -                 | Exporte les événements de la semaine dernière (prioritaire sur `--start` et `--end`)               | Flag    | Optionnel    |
| `--last-month`        | -                 | Exporte les événements du mois dernier (prioritaire sur `--start` et `--end`)                      | Flag    | Optionnel    |
| `--start`             | -                 | Date de début au format YYYY-MM-DD (doit être utilisé avec `--end`)                                | String  | Optionnel    |
| `--end`               | -                 | Date de fin au format YYYY-MM-DD (doit être utilisé avec `--start`)                                | String  | Optionnel    |
| `--export-all`/`-a`        | -                 | Exporte tous les événements de Exchange, y compris ceux sans sujet SFDC Task                        | Flag    | Optionnel    |
| `--output`/`-o`            | `sfdc_task.csv`   | Nom et chemin du fichier CSV de sortie                                                             | String  | Optionnel    |
| `--max-hours-by-day`  | `10`              | Nombre maximal d'heures autorisé par jour                                                         | Integer | Optionnel    |
| `--morning-hour`      | `8`               | Heure de début de la journée utilisée dans le calcul de la durée                                   | Integer | Optionnel    |
| `--evening-hour`      | `22`              | Heure de fin de la journée utilisée dans le calcul de la durée                                     | Integer | Optionnel    |
| `--verbose`/`-v`           | -                 | Mode verbeux (affiche des informations détaillées pendant l'exécution)                             | Flag    | Optionnel    |


---

## 🤝 Contributing

Contributions are welcome! Here are several ways you can contribute:

- **[Submit Pull Requests](https://github/mguyard/SFDC-Task-Import/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.
- **[Report Issues](https://github/mguyard/SFDC-Task-Import/issues)**: Submit bugs found or log feature requests for Sfdc-task-import.

<details closed>
    <summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your GitHub account.
2. **Clone Locally**: Clone the forked repository to your local machine using a Git client.
   ```sh
   git clone https://github.com/mguyard/SFDC-Task-Import
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to GitHub**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.

Once your PR is reviewed and approved, it will be merged into the main branch.

</details>

---

## 📄 License

This project is protected under the [GPL-3.0](https://choosealicense.com/licenses/gpl-3.0/) License. For more details, refer to the [LICENSE](https://github.com/mguyard/SFDC-Task-Import/blob/main/LICENSE) file.

[**Return**](#-quick-links)

---

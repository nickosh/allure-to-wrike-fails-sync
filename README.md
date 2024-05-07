Allure-to-Wrike failures sync
============

:star2: [Features](#star2-features) | :pushpin: [What and why](#pushpin-what-and-why) | :gear: [Run and configuration](#gear-run-and-configuration) | :scroll: [License](#scroll-license)

GitHub action that parsed published Allure reports and created Wrike tasks from failed or broken Allure tests.

<!-- Features -->
:star2: Features
---------------

- Parse published Allure report directly from URL;
- Can extract unique test suite and test name values;
- Script is able to create Wrike folder for each test suite where test case tasks are placed;
- If Wrike task already exists, duplication is not created. Fits well for CI.
- Within each task, brief details about the reasons for the test failure can be found.

<!-- What and why -->
:pushpin: What and why
---------------

In my company QA workflow was decided to create Wrike tasks for each broken or failed test from Allure report. Manually it's a lot of work but can be easily automated so this GHA action was born.

<!-- Run and configuration -->
:gear: Run and configuration
---------------

This repository can be used as GitHub action. Check ```.github/workflows/workflow.yml``` for example of usability.

Action awaiting input of next parameter:
- ```wrike_api_url``` - Wrike API URL. By default it's ```https://www.wrike.com/api/v4/```.
- ```wrike_token``` - Token string to use with the Wrike API. Permanent token is ok. See details [here](https://help.wrike.com/hc/en-us/articles/210409445-Wrike-API).
- ```wrike_root_folder_id``` - ID of the folder where the script will create subfolders for tasks and tasks themselves. Any empty folder will be fine. Note that it's a different ID from the one shown in the Wrike UI. For example: "IEAE2ESRI42RONRN". This type of folder ID can be found using the API: <https://www.wrike.com/api/v4/folders>
- ```allure_report_url``` - String with Allure Report URL that Python script will accept as input. Allure report must be published and should be accessible by URL to script. Script can only parse one report per run in current implementation, but can be run multiple times with different inputs.

<!-- License -->
:scroll: License
---------------

Distributed under the [MIT License](https://spdx.org/licenses/MIT.html) license. See LICENSE for more information.

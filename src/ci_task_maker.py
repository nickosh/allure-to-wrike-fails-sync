from argparse import ArgumentParser
from logging import Logger, StreamHandler
from typing import Any, Dict, List, Optional, Set
from urllib.parse import quote

import requests
from decouple import config
from polling2 import poll

WRIKE_API_URL = config("WRIKE_API_URL", default="https://www.wrike.com/api/v4/")
WRIKE_TOKEN = config("WRIKE_TOKEN")
WRIKE_ROOT_FOLDER_ID = config("WRIKE_ROOT_FOLDER_ID")

WRIKE_AUTH_HEADER = {"Authorization": f"bearer {WRIKE_TOKEN}"}

logger = Logger(__name__)
logger.addHandler(StreamHandler())


def allure_report_check(url: str) -> bool:
    try:
        poll(
            lambda: requests.get(url).status_code == 200,
            step=15,
            timeout=300,
        )
        return True
    except Exception as e:
        logger.error(f"Allure report URL check failed with error: {e}")
        return False


def get_allure_suites(allure_url: str) -> dict:
    suites = requests.get(f"{allure_url}/data/suites.json")
    suites.raise_for_status()
    return suites.json()


def find_failed_tests(suites: dict) -> List[Dict[str, Any]]:
    failed_tests = []
    for child1 in suites["children"]:
        for child2 in child1["children"]:
            suite_name = child2["name"]
            for child3 in child2["children"]:
                for tc in child3["children"]:
                    if "status" in tc and tc["status"] in ["failed", "broken"]:
                        failed_tests.append(
                            {
                                "suite_name": suite_name,
                                "uid": tc["uid"],
                                "parentUid": tc["parentUid"],
                            }
                        )
    return failed_tests


def extract_test_info(allure_url: str, test_uid: str) -> Dict[str, Any]:
    test = requests.get(f"{allure_url}/data/test-cases/{test_uid}.json")
    test.raise_for_status()
    return test.json()


def get_wrike_folders() -> Dict[str, str]:
    folders = requests.get(
        f"{WRIKE_API_URL}/folders/{WRIKE_ROOT_FOLDER_ID}/folders?project=false&descendants=false",
        headers=WRIKE_AUTH_HEADER,
    )
    folders.raise_for_status()
    return {folder["title"]: folder["id"] for folder in folders.json()["data"]}


def create_wrike_folder(folder_name: str) -> str:
    new_folder = requests.post(
        f"{WRIKE_API_URL}/folders/{WRIKE_ROOT_FOLDER_ID}/folders?title={folder_name}",
        headers=WRIKE_AUTH_HEADER,
    )
    new_folder.raise_for_status()
    logger.info(f"New Wrike folder created: {folder_name}")
    return new_folder.json()["data"][0]["id"]


def get_wrike_task_from_folder(folder_id: str) -> Set[str]:
    tasks = requests.get(
        f"{WRIKE_API_URL}/folders/{folder_id}/tasks", headers=WRIKE_AUTH_HEADER
    )
    tasks.raise_for_status()
    return {task["title"] for task in tasks.json()["data"]}


def create_wrike_task(folder_id: str, task_title: str, task_desc: str) -> bool:
    new_task = requests.post(
        f"{WRIKE_API_URL}/folders/{folder_id}/tasks?title={task_title}&description={task_desc}&status=Active",
        headers=WRIKE_AUTH_HEADER,
    )
    new_task.raise_for_status()
    logger.info(f"New Wrike test created: {task_title}")
    return True


def main() -> None:
    parser: ArgumentParser = ArgumentParser(
        description="Parse Allure report and create tasks for QA"
    )
    parser.add_argument(
        "allure_report_url",
        metavar="allure_report_url",
        type=str,
        help="URL of Allure's report",
    )
    args: Optional[str] = parser.parse_args()

    allure_url: str = args.allure_report_url
    if not allure_url:
        raise EnvironmentError("Allure report url not provided!")
    if not allure_report_check(allure_url):
        raise ConnectionError("Allure report url not accessible!")

    wrike_folders = get_wrike_folders()
    failed_tests = find_failed_tests(get_allure_suites(allure_url))
    for test in failed_tests:
        test_data = extract_test_info(allure_url, test["uid"])
        if test["suite_name"] not in wrike_folders.keys():
            folder_id = create_wrike_folder(test["suite_name"])
            wrike_folders[test["suite_name"]] = folder_id
        folder_id = wrike_folders[test["suite_name"]]
        existing_tasks = get_wrike_task_from_folder(folder_id)
        test_clean_name = test_data["name"].split("[")[0]
        if test_clean_name not in existing_tasks:
            allure_report_url = (
                f"{allure_url}/#suites/{test['parentUid']}/{test['uid']}"
            )
            test_desc = f"""
<h1>{test_data['name']}</h1><br/>
<b>status</b>: {test_data['status']}<br/><b>flaky</b>: {test_data['flaky']}<br/>
<b>newFailed</b>: {test_data['newFailed']}<br/><b>newBroken</b>: {test_data['newBroken']}<br/><b>newPassed</b>: {test_data['newPassed']}<br/><br/>
<b>statusMessage</b>: {test_data['statusMessage'][:500] if test_data.get('statusMessage') else None}<br/><br/>Allure link: {allure_report_url}
"""
            assert create_wrike_task(folder_id, test_clean_name, quote(test_desc))
        else:
            logger.info(f"Task for '{test_clean_name}' already exist. Skipped.")


if __name__ == "__main__":
    main()

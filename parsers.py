import pandas as pd
import xml.etree.ElementTree as ET
import json
from datetime import datetime
import os


def parse_playwright_junit(path):
    """Parse Playwright JUnit XML results into DataFrame"""
    if not os.path.exists(path):
        return pd.DataFrame(columns=["suite", "name", "module", "status", "time", "timestamp", "browser"])

    tree = ET.parse(path)
    root = tree.getroot()
    rows = []

    for testsuite in root.findall('testsuite'):
        suite_name = testsuite.get('name', 'unknown')
        suite_timestamp = testsuite.get('timestamp', datetime.now().isoformat())

        for testcase in testsuite.findall('testcase'):
            name = testcase.get('name', 'Unknown Test')
            classname = testcase.get('classname', '')
            time = float(testcase.get('time', 0))
            status = "Passed"

            if testcase.find('failure') is not None:
                status = "Failed"
            elif testcase.find('skipped') is not None:
                status = "Skipped"
            elif testcase.find('error') is not None:
                status = "Error"

            rows.append({
                "suite": "Playwright",
                "name": name,
                "module": classname or suite_name,
                "status": status,
                "time": time,
                "timestamp": suite_timestamp,
                "browser": testsuite.get('hostname', 'unknown')
            })

    return pd.DataFrame(rows)


def parse_test_results_json(path):
    """Parse Playwright test-results.json into DataFrame"""
    if not os.path.exists(path):
        return pd.DataFrame(columns=["suite", "name", "module", "status", "time", "timestamp", "browser"])

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = []
    start_time = data.get('summary', {}).get('startTime', datetime.now().isoformat())

    for t in data.get('tests', []):
        file_path = t.get('file', '')
        if '\\' in file_path:
            module = file_path.split('\\')[-1]
        elif '/' in file_path:
            module = file_path.split('/')[-1]
        else:
            module = file_path

        rows.append({
            "suite": "Playwright",
            "name": t.get('title', 'Unknown'),
            "module": module,
            "status": t.get('status', 'unknown').capitalize(),
            "time": t.get('duration', 0) / 1000,
            "timestamp": start_time,
            "browser": "chromium"
        })

    return pd.DataFrame(rows)


def get_all_test_results(data_dir="data"):
    """Combine all test results from different sources"""
    all_results = []

    # Playwright test-results.json (primary)
    json_path = os.path.join(data_dir, "test-results.json")
    if os.path.exists(json_path):
        json_df = parse_test_results_json(json_path)
        if not json_df.empty:
            all_results.append(json_df)

    # Playwright JUnit XML (secondary, only if no JSON)
    if not all_results:
        junit_path = os.path.join(data_dir, "junit-report.xml")
        if os.path.exists(junit_path):
            junit_df = parse_playwright_junit(junit_path)
            if not junit_df.empty:
                all_results.append(junit_df)

    if all_results:
        return pd.concat(all_results, ignore_index=True)

    return pd.DataFrame(columns=["suite", "name", "module", "status", "time", "timestamp", "browser"])


def calculate_metrics(df):
    """Calculate key QA metrics from test results"""
    if df.empty:
        return {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "pass_rate": 0,
            "avg_execution_time": 0,
            "total_execution_time": 0
        }

    total_tests = len(df)
    passed = len(df[df['status'] == 'Passed'])
    failed = len(df[df['status'] == 'Failed'])
    skipped = len(df[df['status'] == 'Skipped'])

    pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    avg_execution_time = df['time'].mean() if total_tests > 0 else 0
    total_execution_time = df['time'].sum()

    return {
        "total_tests": total_tests,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": round(pass_rate, 2),
        "avg_execution_time": round(avg_execution_time, 2),
        "total_execution_time": round(total_execution_time, 2)
    }

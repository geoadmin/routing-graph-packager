from click.testing import CliRunner

from routing_packager_app.api_v1 import Job
from routing_packager_app.cli import _sort_jobs
from routing_packager_app.cli import register
from .utils import create_new_job, DEFAULT_ARGS_POST


def test_register(flask_app_client, basic_auth_header, script_info, delete_jobs):

    intervals = ("daily", "weekly", "monthly")
    for interval in intervals:
        create_new_job(
            flask_app_client,
            {**DEFAULT_ARGS_POST, "name": interval, "interval": interval},
            basic_auth_header,
            must_succeed=False,
        )

    # register the CLI with the app
    update_f = register(flask_app_client.application)

    # Run the damn thing
    runner = CliRunner()
    result = runner.invoke(update_f, ["daily", "--config", "testing"], obj=script_info)

    if result.exit_code or result.exception:
        raise RuntimeError(f"CLI test wasn't successful. Some hints maybe:\n{result.stdout}")


def test_sort_jobs(flask_app_client, basic_auth_header):
    bboxes = ("0,0,3,3", "0,0,1,1", "0,0,2,2")
    expected_ids = list()
    for bbox in bboxes:
        expected_ids.append(
            create_new_job(
                flask_app_client,
                {**DEFAULT_ARGS_POST, "name": bbox, "description": "blablablabla", "bbox": bbox},
                basic_auth_header,
            )["id"]
        )

    expected_ids = [expected_ids[0], expected_ids[2], expected_ids[1]]
    jobs = Job.query.filter_by(description="blablablabla").all()

    ordered_jobs = _sort_jobs(jobs)
    assert [x.id for x in ordered_jobs] == expected_ids

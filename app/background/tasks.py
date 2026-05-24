from app.background.worker import celery_app
import time

@celery_app.task(name="app.background.tasks.test_task")
def test_task(x, y):
    print("Executing background task...")
    time.sleep(2)
    return x + y
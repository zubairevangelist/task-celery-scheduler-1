# To test project setup
1) git clone https://github.com/zubairevangelist/task-celery-scheduler-1.git
2) docker-compose up


# Celery worker on windows
celery -A tasks.tasks worker --loglevel=info --pool=solo

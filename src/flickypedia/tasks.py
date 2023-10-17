from celery import Celery, Task
from flask import Flask


def celery_init_app(app: Flask) -> Celery:
    """
    Create and configure the Celery app.

    See https://flask.palletsprojects.com/en/2.3.x/patterns/celery/#integrate-celery-with-flask
    """
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

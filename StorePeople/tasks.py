import celery
from sqlalchemy import exists
from sqlalchemy.exc import SQLAlchemyError

from data_access.db import db_session
from data_access.models import Person
from celery.utils.log import get_task_logger
from celery_app import app

logger = get_task_logger(__name__)

class DBSessionTask(celery.Task):
    """A Celery Task that ensures that the connection the the
    database is closed when the task is done
    The db_session is scoped, therefore thread-local
    """

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Handler called after the task returns that release  the connection to the database.
        :param status: Current task state.
        :param retval: Task return value/exception
        :param task_id: Unique id of the task
        :param args: Original arguments for the task
        :param kwargs: Original keyword arguments for the task
        :param einfo:  Exception information
        :type status: str
        :type retval: any
        :type task_id: str
        :type kwargs: dict
        :type einfo: exception
        """
        db_session.remove()


@app.task(base=DBSessionTask)
def add_to_db(full_name: str, email: str):
    """
    Celery task that gets the person data from the broker and stores it in the db.
    It only adds the person if there is not another one with the same email
    :param full_name: full name of person
    :param email: email of person
    """
    logger.info(f"Processing person ({full_name}, {email})")
    if not db_session.query(exists().where(Person.email == email)).scalar():
        try:
            logger.info(f"Storing ({full_name}, {email}) into db")
            db_session.add(Person(full_name=full_name, email=email))
            db_session.commit()
            logger.debug(f"Stored ({full_name}, {email}) into db")
        except SQLAlchemyError:
            db_session.rollback()
            logger.exception(f"Error inserting ({full_name}, {email}) into db")
    else:
        logger.info(f"Person with email {email} is already stored")
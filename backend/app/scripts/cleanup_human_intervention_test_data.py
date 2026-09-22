from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.execution_event import ExecutionEvent

APPLICATION_ID = "0150662c-1d6a-41e1-8a8f-5c7440375693"

db = SessionLocal()

try:
    execution = (
        db.query(ApplicationExecution)
        .filter(ApplicationExecution.application_id == APPLICATION_ID)
        .first()
    )

    if execution is not None:
        db.query(ExecutionEvent).filter(
            ExecutionEvent.execution_id == execution.id
        ).delete(synchronize_session=False)

        db.query(ApplicationExecution).filter(
            ApplicationExecution.id == execution.id
        ).delete(synchronize_session=False)

    db.query(ApplicationPackage).filter(
        ApplicationPackage.application_id == APPLICATION_ID
    ).delete(synchronize_session=False)

    db.query(Application).filter(
        Application.id == APPLICATION_ID
    ).delete(synchronize_session=False)

    db.commit()

    print("Leftover NEEDS_HUMAN test data cleanup: PASS")

finally:
    db.close()

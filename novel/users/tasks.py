import traceback
from celery import states
from celery.exceptions import Ignore
# from django.contrib.auth import get_user_model

from novel.taskapp.celery import app, save_celery_result
from .models import Profile

# User = get_user_model()


@app.task(bind=True, ignore_result=True)
def update_users_votes(self):
    try:
        profiles = Profile.objects.all()
        profiles_prem = profiles.filter(premium=True)
        profiles_nonprem = profiles.filter(premium=False)
        profiles_prem.update(votes=6)
        profiles_nonprem.update(votes=3)
    except Exception as exc:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=exc,
            traceback=traceback.format_exc(),
        )
        raise Ignore()

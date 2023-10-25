#!/bin/bash

new_user() {
    P1=$(python -c "from app.core.security import get_password_hash; print(get_password_hash('$2'))")
    echo "insert into app_user values('$1', 'Guest User', '${P1}', FALSE);"
    echo "insert into organisation_admin(appuser_email, organisation_id, job_title, is_active, is_admin) values ('$1', $3, '', TRUE, FALSE);"
}

# Add a list of new users here:
# Args:
#  - username/email
#  - password
#  - organisation id

new_user "cclw@climatepolicyradar.org" "mypassword" 1


# Generating a new admin service user password

Admin service user password hashes can be generated from the root of the [navigator-backend](https://github.com/ClimatePolicyRadar/navigator-backend)
repository, using the following code snippet

```bash
export SECRET_KEY=secret_key
python -c "from app.service.security import get_password_hash; print(get_password_hash('mypassword'))"
```

where:

- `SECRET_KEY` is a the secret key for the AWS environment you want the user
  password to work on

The resulting hash can be inserted into the `hashed_password` field of the `app_user`
table.

```sql
INSERT INTO app_user VALUES('<email>', '<username>', '<password_hash>', FALSE)
```

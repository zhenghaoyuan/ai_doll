- Python=3.11
- Create a virtualenv with requirements.txt

- Generate db migration configs (no actual change on the db)

  ```
  ENVIRONMENT=dev python manage.py makemigrations ai_art_backend
  ```

- Print the generated db migration configs at 0001 (no actual change on the db)
  ```
  ENVIRONMENT=dev python manage.py sqlmigrate ai_art_backend 0001
  ```
- Apply db migration
  ```
  ENVIRONMENT=dev python manage.py migrate
  ```
- Start the debug interactive command
  ```
  ENVIRONMENT=dev python manage.py shell
  ```
- Start the debug server

  ```
  ENVIRONMENT=dev python manage.py runserver
  ```

- Go to http://127.0.0.1:8000/admin/ for admin page to watch and modify db data

- Static type check

  ```
  ENVIRONMENT=dev  PYTHONPATH="$PYTHONPATH:$PWD" mypy ai_art_backend
  ```

- Format

  ```
  ENVIRONMENT=dev  black ai_art_backend
  ```

- Create superuser for django admin

  ```
  python3 manage.py createsuperuser
  ```

- Copy Files from eb
  ```
  scp -i /Users/MyHome/.ssh/eb.pem ec2-user@<eb-env-ip-address>:/path/to/file .
  ```

## Deployment

- Add frontend URL to CORS setting
- Add the following code block to django.config if there is any changes in the database schema

```
container_commands:
  01_migrate:
    command: "source /var/app/venv/*/bin/activate &&  python manage.py migrate --noinput"
    leader_only: true
  02_createsuperuser:
    command: "source /var/app/venv/*/bin/activate &&  python manage.py createsuperuser --noinput"
    leader_only: true
```

- Add changed files to staging

```
git add -f .env.prod &&
git add -f ai_art_backend/migrations/*.py &&
git add .ebextensions/* &&
git add requirements.txt &&
git add anime_gf/settings.py
eb deploy --staged
```

# Wiki

1. To configure CloudWatch with .ebextensions/cloudwatch.config, refer to the [doc](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/customize-containers-cw.html) to add CloudWatchAgentServerPolicy for EC2 permissions.

- Port forwarding
  ssh -i file -N -L 8001:localhost:8001 username@ip

2. To reload the env variables on EB machines

```
export $(/opt/elasticbeanstalk/bin/get-config --output YAML environment | 
         sed -r 's/: /=/' | xargs)
```

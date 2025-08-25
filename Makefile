# Makefile at project root

# Reset a single app (drop tables, delete migrations, recreate migrations & tables)
reset-app:
	rm -f apps/$(APP)/migrations/0*.py
	python manage.py migrate $(APP) zero
	python manage.py makemigrations $(APP)
	python manage.py migrate $(APP)

# Reset all relevant apps in one go
reset-all:
	for app in core imports partners catalog procurement pricing sales; do \
		rm -f apps/$$app/migrations/0*.py; \
		python manage.py migrate $$app zero; \
		python manage.py makemigrations $$app; \
		python manage.py migrate $$app; \
	done


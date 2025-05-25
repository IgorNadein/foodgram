Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.


python manage.py makemigrations
python manage.py migrate
python manage.py load_ingredients
python manage.py load_tags
python manage.py runserver


source .venv/Scripts/activate

cd frontend
docker build -t igornadein/foodgram_frontend .  
cd ../backend
docker build -t igornadein/foodgram_backend .
cd ../nginx
docker build -t igornadein/foodgram_proxy . 
cd ..
docker push igornadein/foodgram_frontend
docker push igornadein/foodgram_backend
docker push igornadein/foodgram_proxy
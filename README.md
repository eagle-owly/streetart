# Street Art Application

https://medium.com/analytics-vidhya/data-science-for-street-art-7d11cb23dc81

## Building

cd /Users/mike/code/streetart  
docker-compose -f build/docker-compose.yml up --build -d


## Stopping / Cleaning

docker stop $(docker ps | grep streetart | cut -d " " -f1)  
docker rm $(docker ps -a | grep streetart | cut -d " " -f1)  
docker rmi streetart  
docker volume rm build_images && docker volume rm build_mysql_data  


## Running for development

cd src  
python3 -m app  

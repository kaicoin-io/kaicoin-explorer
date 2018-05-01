cd scheduler
sudo forever start -o ../scheduler.log -e ../err-scheduler.log ./scheduler.js
cd ../web
sudo forever start -o ../web.log -e ../err-web.log ./web.js

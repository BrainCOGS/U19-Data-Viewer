# U19-Data-Viewer

[For Developers]

The Data Viewer is currently hosted on `braincogs01.pni.princeton.edu`.
There are two test hostnames (`braincogs01-test0.pni.princeton.edu`) available 
for testing purposes before the final deployment is done on the original website. 

To be able to make changes to the webpage, one needs to have access to the
`braincogs01.pni.princeton.edu` machine. Once the access is provided, you can
login to the machine using the following command:
`ssh <NETID>@braincogs01.pni.princeton.edu`

The website runs on pre-deployed docker containers which are running on Shan's 
workstation. You will find the following containers when you run `docker ps` from
your terminal.
1. 'u19_data_viewer_test_flask-root'
2. 'u19_data_viewer_test_apache'
3. 'u19_data_viewer_flask-root'
4. 'u19_data_viewer_apache'
Here, `u19_data_viewer_flask-root` and `u19_data_viewer_apache` are running the
main website, whereas `u19_data_viewer_test_flask-root` and `u19_data_viewer_test_apache`
are hosting the test0 website.

To make any changes to the website, we recommend to run the modifications on the
test server. Once all changes are approved, changes can be deployed on the new website.

Steps to deploy the test website from your user account:
1. git clone https://github.com/BrainCOGS/U19-Data-Viewer.git 
   OR 
   git clone https://github.com/vathes/U19-Data-Viewer.git
2. Rename `.env.template` to `.env` file
3. Enter one of the running Flask containers using the following command:
    `docker exec -it <container_id> /bin/bash`
4. To find all the .env values, run each of the following statements and paste 
   the values in your .env file:
    echo $SERVICEHOSTNAME
    echo $CASLOGINURL
    echo $CASVALIDATEURL
5. Alternatively, you can copy paste the values from here:
    SERVICEHOSTNAME=braincogs01-test0.pni.princeton.edu
    CASLOGINURL=https://fed.princeton.edu/cas/login
    CASVALIDATEURL=https://fed.princeton.edu/cas/serviceValidate
    COMPOSE_PROJECT_NAME=u19_data_viewer_test
    DJ_HOST=datajoint00.pni.princeton.edu
    DJ_USER=<datajointusername>
    DJ_PASS=<datajointpassword>
6. Run `docker-compose up -d --build` to build a new docker image
7. Go to `braincogs01-test0.pni.princeton.edu` to see the website running.
8. To be able to reflect changes to the website:
    + Make changes to the code
    + `docker-compose down`
    + `docker-compose up`
    + Refresh the webpage to see your changes
    (_The reason that you do not need to build the image again is because in the
    `docker-compose.yml` file we mapped your currently working directory to the 
    docker container directory (`.:/data_viewer`). So, everytime you make a 
    change in your code, it will be reflected on the repository in the docker 
    container_)
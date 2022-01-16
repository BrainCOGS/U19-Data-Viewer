## Developer instructions

### Infrastructure

- The `U19-Data-Viewer` is currently hosted at `braincogs01.pni.princeton.edu`.

- Additionally, there are two test hosts available.
    - `braincogs01-test0.pni.princeton.edu`
    - `braincogs01-test1.pni.princeton.edu`

- The production and test websites are deployed on the `braincogs01.pni.princeton.edu` server.

- Obtain access to server by emailing `pnihelp@princeton.edu`.

- The website runs on Docker containers that are deployed on the server.
    - Production website
        ```
        u19_data_viewer_flask-root
        u19_data_viewer_apache
        ```
    - `test0` website
        ```
        u19_data_viewer_test_flask-root
        u19_data_viewer_test_apache
        ```

- We recommend making modifications on the test website first. Once all changes are tested and approved, these changes can be deployed on the production website.

### Deploy the test website

1. Connect to the `braincogs01.pni.princeton.edu` server.
    ```
    ssh <netID>@braincogs01.pni.princeton.edu
    ```

2. Clone the repository.
    ```
    git clone https://github.com/<BrainCOGS or vathes>/U19-Data-Viewer.git 
    ```

3. Rename the file `.env.template` to `.env`.

4. Copy and modify the following values into the `.env` file.
    ```
    SERVICEHOSTNAME=braincogs01-test0.pni.princeton.edu
    CASLOGINURL=https://fed.princeton.edu/cas/login
    CASVALIDATEURL=https://fed.princeton.edu/cas/serviceValidate
    COMPOSE_PROJECT_NAME=u19_data_viewer_test
    DJ_HOST=datajoint00.pni.princeton.edu
    DJ_USER=<datajointusername>
    DJ_PASS=<datajointpassword>
    ```

5. Build the new Docker image and start the container.
    ```
    docker-compose up -d --build
    ```

6. View the deployed website in your browser at `braincogs01-test0.pni.princeton.edu`.

### Modify the test website

1. Make relevant changes to the code.

2. Stop the container.
    ```
    docker-compose down
    ```

3. Start the container.
    ```
    docker-compose up
    ```

4. Refresh the webpage.

+ Note: The Docker image does not need to be rebuilt each time you modify the source code because the source code directory on the host machine is mounted to the Docker container (see the `docker-compose.yml` file's `volume` key).
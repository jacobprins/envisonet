# Envisonet

## <ins>**About**</ins> 
Envisonet is the final GNG1103 project for Group 8. This repo contains all the code used for this project. It should be noted that this repo was uploaded to an AWS EC2 instance to allow for our website to be visable on the domain "[envisonet.com](envisonet.com)". This is the public repo of this project. All files were developed in a private repo previously.  

### Envisonet Team  
Badir Budair, Emily Boyd, [Ian Haines](https://github.com/Hainzie), [Jacob Prins](https://github.com/jacobprins), and Mariano Suarez  

### Special Thanks To  
[Cyrus Choi](https://github.com/cyruschoisy) and [Sébastien Girard](https://github.com/sebastiengrd)

### References  
See [references.txt](references.txt)

## <ins>**EC2 Info**</ins>  
### **Application and OS Images**  
OS: Amazon Linux 2023 AMI  
Architecture: 64-bit (x86)  

### **Instance Type**  
t2.micro  

### **Storage**  
8 GiB gp3  

## <ins>**Other Requirements**</ins>  
### FFMPEG  
- ffmpeg is required. For installation on the EC2 above, see *How to install FFMPEG on EC2 running Amazon Linux?* [\[4\]](https://www.maskaravivek.com/post/how-to-install-ffmpeg-on-ec2-running-amazon-linux/). Notably, a symlink for ffprobe must be created as well, so after step 6, run: `ln -s /usr/local/bin/ffmpeg/ffprobe /usr/bin/ffprobe`  

### NGINX  
- If running on an EC2 instance, configure nginx to reverse-proxy localhost:8000, see steps 1-3 of *How to set up Nginx and Gunicorn to make the Python Flask app on AWS EC2 accessible web pages* [\[2\]](https://medium.com/@ihenrywu.ca/how-to-set-up-nginx-and-gunicorn-to-make-the-python-flask-app-on-aws-ec2-accessible-web-pages-92fa24a77a88)


## <ins>**Guide to Running the System**</ins> 

1. Create a virtual environment in the "FlaskServerReImagined" *(setup only)*:  
   `python3 -m venv venv/`

2. Activate the virtual environment:  
   `source venv/bin/activate`

3. Install packages *(setup only)*:  
   `pip install --upgrade pip`  
   `pip install -r requirements.txt`  

4. Configure the database *(setup only)*:  
   `python3 config.py`  

5. To prevent the creation of "__pycache__" folders:  
   `export PYTHONDONTWRITEBYTECODE=1`

6. Assign **OpenAI** and **xAI** API key environment variables:  
   `export OPENAI_API_KEY=<put_the_key_here>`  
   `export xAI_API_KEY=<put_the_key_here>`  

8. Start the server:  
   `gunicorn --workers=2 app:app`  

9. Stop the server:  
   `ctrl+c`  

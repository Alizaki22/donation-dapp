FROM node:18

WORKDIR /app

COPY . .

# install python backend only
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install --break-system-packages flask web3 flask-cors python-dotenv

EXPOSE 5000 8080

CMD ["bash"]
<h1>Publication Storage App</h1>
An application for storing publications with its data and files created at WUT.

<h1>Techonologies</h1>

- Python
- Flask
- Java
- JavaFX
- Redis
- Docker
- Maven
- HTML5
- CSS
- Javascript

<h1>Description</h1>
Application consists of:

- REST API (in folder "api")
- web client in Python, Flask (in folder "web")
- desktop client in JavaFX (in folder "P3-JavaFX")

<h1>How to run</h1>
In order to run this project you need to add the following lines to your etc/hosts file:
<pre>
127.0.0.1 web.company.com
127.0.0.1 api.company.com
</pre>

Also, when using VirtualBox you need to forward ports mentioned below:
<pre>
"host port" : "guest port"
"443:443"
"6381:6381"
"6380:6380"
"6379:6379"
</pre>

Then you can start Docker with the command:
<pre>
docker-compose up --build
</pre>

Next thing you need to do is to create your user by connecting with Redis database typing:
<pre>
redis-cli -h localhost -p 6379
</pre>

and adding your username and password, for example:
<pre>
set login pass1234
</pre>

The application is available at:
<pre>
https://web.company.com
</pre>

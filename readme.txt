Przed uruchomieniem Dockera, w przypadku korzystania z maszyny wirtualnej VirtualBox należy przekierować porty:
port hosta: port gościa
- "443:443"
- "6381:6381"
- "6380:6380"
- "6379:6379"

W pliku /etc/hosts trzeba również dodać następujące linie:
127.0.0.1	api.company.com
127.0.0.1	web.company.com

Docker należy uruchomić poleceniem: "docker-compose up --build" w folderze z projektem.

Następnie, po uruchomieniu Dockera, należy połączyć się z bazą danych Redis przez polecenie:
"redis-cli -h localhost -p 6379"

oraz dodać przykładowego użytkownika oraz hasło np. "user", "password" przez polecenie:
"set user password"

Aplikacja jest dostępna pod adresem:
https://web.company.com


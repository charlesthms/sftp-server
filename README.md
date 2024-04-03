# <p align="center">SFTP Server</p>
  
This is a simple SFTP server using **paramiko**. It doesn't support proper login system since every credentials will be accepted. 


## 🧑🏻‍💻 Usage

First, you need to update the server adress based on you local network

```python
HOST = "127.0.0.1"
```
Then you can start the server
```bash
python server.py
```
Finally you can use any SFTP client on port 2222
```bash
sftp -P 2222 127.0.0.1
```


## 🙇 Context

This projet was made during my Master 1 at University Paris-Est Créteil
        

# ![kokot files](https://files.kokot.club/files/uploads/1bqjmg4)

A stupid simple file hosting app

### Features
- Modern UI, including user dashboard and an admin panel
- Multiple languages support
- Invite system for users
- Expressive social media embeds (Discord, Twitter)
- Integrations with screen capture tools (ShareX)
- Rich file displays (Sound, Text, Video)
- Cloudflare Turnstile support
- Upload metadata removal
- Anonymous mode
- Temporary uploads

### Powered by
- Flask
- SQLite
- mithril.js
- Docker

# Deploying
1. Clone
```sh
git clone --recurse-submodules https://github.com/kokot-club/host
```

2. Populate your `.env` file accordingly to `.env.example`

3. Build
```sh
docker build -t kokot-host .
```

4. Run
```sh
docker run -p 8484:8484 kokot-host
```

5. Visit [localhost:8484](http://localhost:8484/)

# Reverse proxy (nginx)
```nginx
server {
    listen 80;
    server_name files.*;

    locaiton / {
        proxy_set_header X-Host $host;
        proxy_set_header X-Real-Ip $remote_addr;

        proxy_pass http://127.0.0.1:8484;
    }
}
```
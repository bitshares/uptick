****************************
Public API this.uptick.rocks
****************************

this.uptick.rocks
#################

The public API node at ``this.uptick.rocks`` serves as an *experimental endpoint*. It is offered for free to our best efforts.

You may

* use it for prototyping of your tools
* use it for testing

You may not:

* expect it to be reliable
* spam it with unnecessary load

Running your own node
#####################

You can run a similar node with rather low efforts assuming you know how to compile the `official bitshares daemon <https://github.com/bitshares/bitshares2/>`_

BitShares Daemon
~~~~~~~~~~~~~~~~

This is the ``config.ini`` file for the witness_node:

::

    rpc-endpoint = 127.0.0.1:28090
    enable-stale-production = false
    required-participation = false
    bucket-size = [15,60,300,3600,86400]
    history-per-size = 1000

This opens up the port ``28090`` for localhost. Going forward, you can either open up this port directly to the public, or tunnel it through a webserver (such as nginx) to add SSL on top, do load balancing, throttling etc.

Nginx Webserver
~~~~~~~~~~~~~~~

``this.uptick.rocks`` uses a nginx server to 

* provide a readable websocket url
* provide SSL encryption
* perform throttling
* allow load balancing

The configuration would look like this

::

   upstream websockets {       # load balancing two nodes
           server 127.0.0.1:5090;
           server 127.0.0.1:5091;
   }

   server {
       listen 443 ssl;
       server_name this.uptick.rocks;
       root /var/www/html/;

       keepalive_timeout 65;
       keepalive_requests 100000;
       sendfile on;
       tcp_nopush on;
       tcp_nodelay on;

       ssl_certificate /etc/letsencrypt/live/this.uptick.rocks/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/this.uptick.rocks/privkey.pem;
       ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
       ssl_prefer_server_ciphers on;
       ssl_dhparam /etc/ssl/certs/dhparam.pem;
       ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA';
       ssl_session_timeout 1d;
       ssl_session_cache shared:SSL:50m;
       ssl_stapling on;
       ssl_stapling_verify on;
       add_header Strict-Transport-Security max-age=15768000;

       location ~ ^(/|/ws) {
           limit_req zone=ws burst=5;
           access_log off;
           proxy_pass http://websockets;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_next_upstream     error timeout invalid_header http_500;
           proxy_connect_timeout   2;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }

       location ~ /.well-known {
           allow all;
       }

   }

As you can see from the ``upstream`` block, the node actually uses a load balancing and failover across **two** locally running ``witness_node`` nodes.
This allows to upgrade the code and reply one one while the other takes over the full traffic, and vise versa.


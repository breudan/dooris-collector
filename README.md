# collect dooris sensor data and output an aggregated version.

## setup
* `virtualenv venv`
* `source venv/bin/activate`
* `pip install -r requirements.txt`
* `cp dooris.cfg.example dooris.cfg`
* edit dooris.cfg
* `python collector.py &`

## output JSON schema

    {
        "name": "Dooris",
        "properties": {
            "apiversion": {
               "type": "number",
               "description": "used dooris API version",
               "required": true
            },
            "door": {
                "type": "object",
                "description": "door status",
                "required": false,
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "current door status. 0: door is open; 1: door is closed; -1 error",
                        "required": true
                    },
                    "last_change": {
                        "type": "string",
                        "description": "unix timestamp of last status change",
                        "required": true
                    },
                    "last_update": {
                        "type": "string",
                        "description": "unix timestamp of last sensor read",
                        "required": true
                    }
                }
            },
            "router": {
                "type": "object",
                "description": "router status",
                "required": false,
                "properties": {
                    "dhcp": {
                        "type": "string",
                        "description": "number of active dhcp leases (or -1 on error)",
                        "required": true
                    },
                    "last_change": {
                        "type": "string",
                        "description": "unix timestamp of last status change",
                        "required": true
                    },
                    "last_update": {
                        "type": "string",
                        "description": "unix timestamp of last sensor read",
                        "required": true
                    }
                }
            }
        }
    }

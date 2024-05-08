from adistools.adisconfig import adisconfig
from adistools.log import Log

from flask import Flask, request, Response
from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime

class resp_get:
    project_name='adistools-resp_get'
    def __init__(self):
        self._config=adisconfig('/opt/adistools/configs/adistools-resp_get.yaml')
        self._log=Log(
            parent=self,
            backends=['rabbitmq_emitter'],
            debug=self._config.log.debug,
            rabbitmq_host=self._config.rabbitmq.host,
            rabbitmq_port=self._config.rabbitmq.port,
            rabbitmq_user=self._config.rabbitmq.user,
            rabbitmq_passwd=self._config.rabbitmq.password,
        )  

        self._mongo_cli=MongoClient(
            self._config.mongo.host,
            self._config.mongo.port,
        )

        self._mongo_db=self._mongo_cli[self._config.mongo.db]
        self._campaigns=self._mongo_db['resp_get_campaigns']
        self._metrics=self._mongo_db['resp_get_metrics']

    def add_metric(self,campaign_uuid, campaign_name, remote_addr, user_agent, time, args, form):
        document={
            "args": args,
            "form": form,
            "campaign_uuid": campaign_uuid,
            "campaign_name": campaign_name,
            "time": {
                "timestamp": time.timestamp(),
                "strtime": time.strftime("%m/%d/%Y, %H:%M:%S")
                },
            "client_details": {
                "remote_addr": remote_addr,
                "user_agent": user_agent,
                }
            }

        self._metrics.insert_one(document)

    def get_campaign(self, campanign_uuid):
        query={
            'campaign_uuid' : campanign_uuid
        }
        return self._campaigns.find_one(query)


resp_get=resp_get()
application=Flask(__name__)

@application.route("/<campaign_uuid>", methods=['GET', 'POST'])
def track(campaign_uuid):
    
    data=resp_get.get_campaign(campaign_uuid)
    if data:
        time=datetime.now()
        campaign_uuid=data['campaign_uuid']
        campaign_name=data['campaign_name']
        user_agent=str(request.user_agent)

        if request.headers.getlist("X-Forwarded-For"):
            remote_addr=request.headers.getlist("X-Forwarded-For")[0]
        else:
            remote_addr=str(request.remote_addr)
        
        resp_get.add_metric(
        	campaign_uuid=campaign_uuid,
            campaign_name=campaign_name,
            remote_addr=remote_addr,
            user_agent=user_agent,
            time=time,
            args=request.args,
            form=request.form
            )


        return "ok"
    else:
        return ""

@application.route("/", methods=['GET'])
def index():
    return ""
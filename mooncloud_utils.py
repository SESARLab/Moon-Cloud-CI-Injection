#!/usr/bin/env python
import sys
import time
import requests

class MoonCloudUtils:
    mooncloud_api_login_endpoint="https://api.v2.moon-cloud.eu/user/login-token/"
    mooncloud_api_evaluation_start_endpoint="https://api.v2.moon-cloud.eu/evaluation-rules/{uer_id}/start/"
    mooncloud_api_evaluation_endpoint="https://api.v2.moon-cloud.eu/evaluation-rules/{uer_id}/"
    max_attempt_number=10

    @staticmethod
    def getToken(user,password):
        response=requests.post(url=MoonCloudUtils.mooncloud_api_login_endpoint,headers={"Content-Type":"application/json"},json={
            "username":user,
            "password":password
        })
        if response.status_code==200:
            response_obj=response.json()
            return response_obj["token"]
        else:
            print(f"Error occured, Status Code:{response.status_code}, Reason:{response.reason}")
            exit(1)

    @staticmethod
    def startEvaluation(token,uer_id,wait_result):
        initial_result_number=None
        if wait_result:
            initial_result_number=MoonCloudUtils.getEvaluationResult(token=token,uer_id=uer_id)[1]
        response=requests.put(url=MoonCloudUtils.mooncloud_api_evaluation_start_endpoint.format(uer_id=uer_id),headers={
            "Content-Type":"application/json",
            "Authorization":"Token "+token})
        if response.status_code==200:
            response_obj=response.json()
            if wait_result:
                new_result=False
                tmp_result=None
                t_counter=0
                while not new_result and t_counter<MoonCloudUtils.max_attempt_number:
                    tmp_result,tmp_result_number=MoonCloudUtils.getEvaluationResult(token=token,uer_id=uer_id)
                    if tmp_result_number==(initial_result_number+1):
                        new_result=True
                    print("Waiting for evaluation completion...")
                    time.sleep(10)
                    t_counter=t_counter+1                
                if t_counter>=MoonCloudUtils.max_attempt_number:
                    print("Max attempt number exceeded")
                    exit(1)
                return {
                    "status":response_obj["result"],
                    "result":tmp_result["result"],
                }
            else:
                return {
                    "status":response_obj["result"],
                }
        else:
            print(f"Error occured, Status Code:{response.status_code}, Reason:{response.reason}")
            exit(1)
    
    @staticmethod
    def getEvaluationResult(token,uer_id):
        response=requests.get(url=MoonCloudUtils.mooncloud_api_evaluation_endpoint.format(uer_id=uer_id),headers={
            "Content-Type":"application/json",
            "Authorization":"Token "+token})
        if response.status_code==200:
            response_obj=response.json()
            return response_obj,len(response_obj["tests"][0]["execution_results"])
        else:
            print(f"Error occured, Status Code:{response.status_code}, Reason:{response.reason}")
            exit(1)

if __name__ == "__main__":
    # python mooncloud_utils.py get-token --user <user> --password <password>
    if len(sys.argv)==6 and sys.argv[1]=="get-token" and sys.argv[2]=="--username" and sys.argv[4]=="--password":
        token=MoonCloudUtils.getToken(user=sys.argv[3],password=sys.argv[5])
        print(token)
    # python mooncloud_utils.py start-evaluation --token <token> --uer-id <uer_id>
    elif len(sys.argv)==6 and sys.argv[1]=="start-evaluation" and sys.argv[2]=="--token" and sys.argv[4]=="--uer-id":
        response=MoonCloudUtils.startEvaluation(token=sys.argv[3],uer_id=sys.argv[5],wait_result=False)
        assert response["status"]=="started", "Something went wrong"
        print("Evaluation started")
    # python mooncloud_utils.py start-evaluation --token <token> --uer-id <uer_id> --wait-result
    elif len(sys.argv)==7 and sys.argv[1]=="start-evaluation" and sys.argv[2]=="--token" and sys.argv[4]=="--uer-id" and sys.argv[6]=="--wait-result":
        response=MoonCloudUtils.startEvaluation(token=sys.argv[3],uer_id=sys.argv[5],wait_result=True)
        assert response["status"]=="started", "Something went wrong"
        print("Evaluation result:"+("true" if response["result"]==True else "false"))
        assert response["result"], "Evaluation result false"
    else:
        print("Params not valid")
        exit(1)
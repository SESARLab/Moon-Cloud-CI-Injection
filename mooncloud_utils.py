#!/usr/bin/env python
import math
import sys
import time
import requests
import argparse

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
        response.raise_for_status()
        return response.json()["token"]

    @staticmethod
    def startEvaluation(token,uer_id,wait_result) -> bool:
        execution_result=None
        initial_result_number=None
        if wait_result:
            initial_result_number=MoonCloudUtils.getEvaluationResult(token=token,uer_id=uer_id)[1]
        response=requests.put(url=MoonCloudUtils.mooncloud_api_evaluation_start_endpoint.format(uer_id=uer_id),headers={
            "Content-Type":"application/json",
            "Authorization":"Token "+token})
        response.raise_for_status()
        print("Evaluation started correctly")
        start_evaluation_response_obj=response.json()
        if wait_result:
            new_result_flag=False
            tmp_result=None
            t_counter=0
            while not new_result_flag and t_counter<MoonCloudUtils.max_attempt_number:
                print("Waiting for evaluation completion...")
                time.sleep(10)
                tmp_result,tmp_result_number=MoonCloudUtils.getEvaluationResult(token=token,uer_id=uer_id)
                if tmp_result_number==(initial_result_number+1):
                    new_result_flag=True
                else:
                    t_counter=t_counter+1
            if t_counter>=MoonCloudUtils.max_attempt_number:
                raise TimeoutError("Max attempt number exceeded")
            execution_result={
                "evaluation_started":True if start_evaluation_response_obj["result"]=="started" else False,
                "evaluation_result":True if tmp_result["result"]==True else False
            }
        else:
            execution_result={
                "evaluation_started":True if start_evaluation_response_obj["result"]=="started" else False
            }
        return execution_result
    
    @staticmethod
    def getEvaluationResult(token,uer_id):
        response=requests.get(url=MoonCloudUtils.mooncloud_api_evaluation_endpoint.format(uer_id=uer_id),headers={
            "Content-Type":"application/json",
            "Authorization":"Token "+token})
        response.raise_for_status()
        response_obj=response.json()
        tests_ex_res_len_sum=0
        tests_ex_res_len_avg=0
        for test in response_obj["tests"]:
            tests_ex_res_len_sum=tests_ex_res_len_sum+len(test["execution_results"])
        tests_ex_res_len_avg=math.floor(tests_ex_res_len_sum/len(response_obj["tests"]))
        return response_obj,tests_ex_res_len_avg

def exitWithError(error_str):
    print("Error occured: "+error_str, file=sys.stderr)
    exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get token by providing username and password")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # get-token option
    get_token_parser = subparsers.add_parser("get-token", help="Get token")
    get_token_parser.add_argument("--username", required=True, help="Username")
    get_token_parser.add_argument("--password", required=True, help="Password")

    # start-evaluation option
    start_evaluation_parser = subparsers.add_parser("start-evaluation", help="Get token")
    start_evaluation_parser.add_argument("--token", required=True, help="Token")
    start_evaluation_parser.add_argument("--uer-id", required=True, help="UER ID")
    start_evaluation_parser.add_argument("--wait-result", required=False, action="store_true", help="Wait for evaluation result")

    args = parser.parse_args()

    if args.command == "get-token":
        try:
            print(MoonCloudUtils.getToken(user=args.username,password=args.password))
        except Exception as e:
            exitWithError(str(e))
    elif args.command == "start-evaluation":
        if not args.wait_result:
            try:
                response=MoonCloudUtils.startEvaluation(token=args.token,uer_id=args.uer_id,wait_result=False)
                assert response["evaluation_started"], "An error occured during evaluation starting"
                print(response)
            except Exception as e:
                exitWithError(str(e))
        else:
            try:
                response=MoonCloudUtils.startEvaluation(token=sys.argv[3],uer_id=sys.argv[5],wait_result=True)
                assert response["evaluation_started"], "An error occured during evaluation starting"
                assert response["evaluation_result"], "Evaluation failed"
                print(response)
            except Exception as e:
                exitWithError(str(e))
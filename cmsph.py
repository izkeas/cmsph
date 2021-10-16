#!/usr/bin/python3
import argparse
import requests
import json

from requests.api import head

parser = argparse.ArgumentParser(description='cmsp tricks')
parser.add_argument('-l', '--login',action='store', metavar='user:password')
parser.add_argument('-p', '--apikey',action='store', metavar='key')
parser.add_argument('-a', '--answerall',action='store_true')
parser.add_argument('-u', '--user-info')
parser.add_argument('-t', '--get-all-tasks', action='store_true')
parser.add_argument('-r', '--get-task-info')
parser.add_argument('-nv', "--non-verbose", action='store_true')
parser.add_argument('-nc', "--no-color", action='store_true')

class C:
    pur = '\033[95m'
    blu = '\033[94m'
    cya = '\033[96m'
    gre = '\033[92m'
    ora = '\033[93m'
    red = '\033[91m'
    ec = '\033[0m'
    bold = '\033[1m'
    underline = '\033[4m'

VERBOSITY=1
COLOR=1

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
    "Accept" : "application/json, text/plain, */*",
    "Host" : "cmspweb.ip.tv",
    "Origin": "https://cmspweb.ip.tv/",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache, no-store, must-revalidate"
}

room="rfe8d167422a5942fd-l"
s = requests.Session()
s.headers = headers

def printJson(dict):
    print(json.dumps(dict, indent=4))

def printc(string, color:C):
    if (COLOR == 0):
        print(string)
    else:
        print(color + string + C.ec)

def setc(color:C):
    if (COLOR == 0):
        pass; return
    print(color, end="")

def endc():
    if (COLOR == 0):
        pass; return
    print(C.ec, end="")

def login(username, password):
    printc("> Authenticating", C.ora)

    payload = f"realm=edusp&platform=webclient&username={username}&password={password}"
    s.headers['Content-Type'] = "application/x-www-form-urlencoded; charset=UTF-8"
    s.headers['Referer']      = "https://cmspweb.ip.tv/login"
    res = s.post("https://cmspweb.ip.tv/", data=payload)

    if (res.status_code == 200):
        printc("> Successifuly Logged-In", C.gre)
    else:
        printc(f"# Error while login {res}", C.red)
        exit(0)

    return res

def getInitial()->dict:
    printc("> Getting Initial informations", C.ora)
    payload = "data%5Baction%5D=getInitial&data%5BnewTab%5D=true"

    res = s.post("https://cmspweb.ip.tv/g/getInitial", payload)

    if (res.status_code != 200):
        printc(f"Error getting Initial {res}", C.red)
        return {}
    
    return res.json()

def getAllTasks(answers=False):
    s.headers['Host'] = "edusp-api.ip.tv"
    s.headers['Accept-Language'] = "en-US,en;q=0.5"
    s.headers['Referer'] = "https://cmsp-tms.ip.tv/"
    s.headers['TE'] = "Trailers"
    s.headers['If-None-Match'] = "W/\"2d37-1e2L4JEu4xepuXF0QS+d+ghu7A8\""

    printc("Getting tasks", C.blu)
    tasks = s.get(f"https://edusp-api.ip.tv/tms/task?type=task&publication_target[]=212&without_answer=false")
    
    if (VERBOSITY > 0):
        printJson(tasks.json())
    else: 
        print(f"{tasks.json().__len__()} tasks.")

    return tasks.json()

def getTask(id_, answers=False):
    s.headers['Referer'] = "https://cmsp-tms.ip.tv/"
    s.headers['TE'] = "Trailers"
    s.headers['Host'] = "edusp-api.ip.tv"
    id_ = str(id_)
    dict = s.get(f"https://edusp-api.ip.tv/tms/task/{id_}?with_questions={answers}")
    return dict.json()

def getUserInfo(nick:str):
    dict= s.get(f"https://edusp-api.ip.tv/tms/answer?nick={nick}&room={room}")
    printJson(dict.json())

def getTaskAnswersPayload(id_=None, dict=None):
    if (id_) and not dict:
        dict = getTask(id_, answers=True)

    questions = dict["questions"]
    payload = {}
    payload['accessed_on'] = "room"
    payload['executed_on'] = "rfe8d167422a5942fd-l"
    payload['duration'] = 0.5
    payload['answers'] = {}

    for question in questions:
        qid = question["id"]
        answers = {}
        count = 0

        try:
            for key, value in question["options"].items():
                if value["answer"] == True:
                    answers[str(count)] = True
                else:
                    answers[str(count)] = False
                count += 1
        except:
            continue

        payload["answers"][str(qid)] = \
        {
            "question_id":qid,
            "question_type":"single",
            "answer": answers,
        }
    return payload

def postTaskAnswers(id_, payload):
    id_ = str(id_)
    s.headers['Content-type'] = "application/json"
    s.headers['TE'] = "Trailers"
    res = s.post(f"https://edusp-api.ip.tv/tms/task/{id_}/answer", data=payload)
    return res.json()

def answerAll():
    printc("> Listing All Tasks", C.cya)
    
    success=0
    errors=0

    for task in getAllTasks():
        print('\n')

        id_ = task["id"]
        title = task["title"]

        answers = json.dumps(getTaskAnswersPayload(id_=id_))

        printc(f"{title}  id:{id_}", C.cya)
        printc(f"> Payload:", C.cya)
        printc(answers, C.cya)
        printc("> Posting Payload...", C.ora)

        res = postTaskAnswers(id_, answers)

        try:
            er_str = res["errors"][0]["message"]
            printc(f"An error Ocurred: {er_str}", C.red)
            errors += 1
        except :
            printc(F"Successfully Answered!", C.gre)
            print(res['result_score'])
            success += 1
    
    print(f"{success} Tasks successfully answered!")
    print(f"{errors} Tasks That returned error or already answered previously.")

def main():
    global VERBOSITY, COLOR

    args = parser.parse_args()

    loginstr = args.login
    apikey = args.apikey
    answerall = args.answerall
    user = args.user_info
    get_tasks = args.get_all_tasks
    task = args.get_task_info

    if args.non_verbose:
        VERBOSITY=0
    if args.no_color:
        COLOR=0

    if loginstr:
        loginstr = loginstr.split(":")
        login(loginstr[0], loginstr[1])

        setc(C.gre)
        printJson(s.cookies.items())
        endc()

        initial = getInitial()
        xapikey = initial['auth_token']
        s.headers["x-api-key"] = xapikey

        setc(C.gre)
        printJson(initial)
        endc()
    
    if apikey:
        print("Loging with x-api-key")
        s.headers['x-api-key'] = apikey

    if answerall == True:
        answerAll()

    if user != None:
        printJson(getUserInfo(user))

    if get_tasks == True:
        getAllTasks()

    if task != None:
        printJson(getTask(task, answers=True))
    

if __name__ == "__main__":
    main()


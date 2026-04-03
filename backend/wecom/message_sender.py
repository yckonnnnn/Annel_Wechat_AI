import requests
from wecom.token_manager import token_manager
from backend.core_config import wecom_config
class MessageSender:
    SEND_URL="https://qyapi.weixin.qq.com/cgi-bin/message/send"
    MSG_TPL_URL="https://qyapi.weixin.qq.com/cgi-bin/externalcontact/add_msg_template"
    def send_text_message(self,to_user,content,agent_id=None):
        token=token_manager.get_token()
        if not token:return False
        payload={"touser":to_user,"msgtype":"text","agentid":int(agent_id or wecom_config["agent_id"]),"text":{"content":content},"safe":0}
        try:
            r=requests.post(self.SEND_URL,params={"access_token":token},json=payload,timeout=10)
            r.raise_for_status();d=r.json()
            return d.get("errcode")==0
        except Exception as e:
            print(f"[Sender] {e}");return False
    def send_proactive_msg(self,sender,external_ids,content,attachments=None):
        token=token_manager.get_token()
        if not token:return{"success":False,"errmsg":"no token"}
        payload={"chat_type":"single","external_userid":external_ids,"sender":sender,"text":{"content":content}}
        if attachments:payload["attachments"]=attachments
        try:
            r=requests.post(self.MSG_TPL_URL,params={"access_token":token},json=payload,timeout=10)
            r.raise_for_status();d=r.json()
            if d.get("errcode")==0:return{"success":True,"msgid":d.get("msgid",""),"fail_list":d.get("fail_list",[])}
            return{"success":False,"errcode":d.get("errcode"),"errmsg":d.get("errmsg","")}
        except Exception as e:
            return{"success":False,"errmsg":str(e)}
    def get_send_result(self,msgid,userid):
        return {"success":False,"errmsg":"not supported for single chat"}

    def send_external_text_message(self, sender: str, external_userid: str, content: str) -> dict:
        """
        代员工给单个外部客户发送文本消息
        接口: POST https://qyapi.weixin.qq.com/cgi-bin/externalcontact/message/send
        """
        token = token_manager.get_token()
        if not token:
            return {"success": False, "errmsg": "no token"}

        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/message/send"
        payload = {
            "sender": sender,
            "external_userid": external_userid,
            "text": {"content": content},
        }

        try:
            r = requests.post(url, params={"access_token": token}, json=payload, timeout=10)
            r.raise_for_status()
            d = r.json()
            if d.get("errcode") == 0:
                return {"success": True, "msgid": d.get("msgid", "")}
            return {"success": False, "errcode": d.get("errcode"), "errmsg": d.get("errmsg", "")}
        except Exception as e:
            return {"success": False, "errmsg": str(e)}


message_sender = MessageSender()

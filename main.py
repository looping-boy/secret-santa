import json
import base64
import urllib.parse


def lambda_handler(event, context):
    req = event['requestContext']['http']
    #response = json.dumps(event['requestContext']['http'])
    path_segments = req['path'].split('/')
    

    # Here you get the status of the sent email:
    if req['method'] == 'POST' and event['body']:
        body = base64.decodebytes(event['body'].encode()).decode()
        # super hacky but whatever
        discard_len = len('message_body=')
        message_body = body[discard_len:]
        message_body = urllib.parse.unquote_plus(message_body, "ISO-8859-1")
        token = req['path'].split('/')[-2]
        u = get_user(token)
        receiver_name = u['receiver_name']
        current_user = u['user']
        
        direction = path_segments[4]
        
        subject = "Secret Santa Olléon : "
        
        if direction == 'toReceiver':
            subject += "Message de ton Père Noël"
            destination = u['receiver_email']    
            destinataire_token = u['receiver_token']
        else:
            subject +=  f'Message de {current_user}'
            destination = u['santa_email']
            destinataire_token = u['santa_token']
        copy = USERS.get(current_user, 'User not found')
        
        subjectcc = "Secret Santa Olléon"
        subjectcc += f' : Message envoyé à {receiver_name}' if path_segments[4] == 'toReceiver' else ' : Message envoyé au Père Noël'
        
        message_body_with_footer = f"{message_body}<br><br>*+*+*+*+*<br>* Ne réponds pas directement à cet email !<br>"
        message_body_with_footer += f'* Pour répondre utilise <a href="https://7r9qj216hb.execute-api.eu-west-3.amazonaws.com/default/lamagiedenoel/{destinataire_token}">ta page secrète !</a>'
    
        send_email(message_body_with_footer, subject, destination)
        send_email(message_body, subjectcc, copy)
        response = make_success_html(True)
        
        # try:
        #     post_data = json.loads(event['body'])
        #     token = req['path'].split('/')[-2]
        #     u = get_user(token)
            # receiver_name = u['receiver_name']
            # current_user = u['user']
            
        #     body = post_data['value']
        #     subject = "Secret Santa Olléon"
        #     subject += " : Message From Your Santa" if path_segments[4] == 'toReceiver' else f' : Message From {current_user}'
        #     destination = u['receiver_email'] if path_segments[4] == 'toReceiver' else u['santa_email']
        #     copy = USERS.get(current_user, 'User not found')
            
        #     subjectcc = "Secret Santa Olléon"
        #     subjectcc += f' : Message you sent to {receiver_name}' if path_segments[4] == 'toReceiver' else ' : Message you sent to your Santa'
            
        #     send_email(body, subject, destination)
        #     send_email(body, subjectcc, copy)
        # except json.JSONDecodeError as e:
        #     print(f"Error decoding JSON: {e}")
    
    else:
        # This route should never be accessed :
        if req['path'] == '/default/lamagiedenoel':
            response = indexLooping()
            
        # Here you are in Santa or Receiver and you can write a message : 
        elif len(path_segments) == 5 and path_segments[4] in ('toReceiver', 'toSanta'):
            response = write_message_page(path_segments[3], path_segments[4])
    
        # Here you choose Santa or Receiver message :
        elif req['path'].startswith('/default/lamagiedenoel/'):
            response = choose_message_page(req['path'].split('/')[-1], req['method'])        

    # Launch :
    #sendStartMailToEveryone()

    return {
        "isBase64Encoded": False,
        'statusCode': 200,
        'body': response,
        'headers': {
            'Content-Type': 'text/html',
        },
    }

def index():
    resp = "Mais qui est-ce donc?"
    resp += "<ul>"
    for u, h in HASHED_USERS.items():
        resp += f'<li><a href="/default/lamagiedenoel/{h}">{u}</a></li>'
    resp += "</ul>"
    return resp
    
    
# def authenticated(token, method):
#     u = get_user(token)
#     resp = f"<h3>Bonjour {u['user']} !</h3>"
#     resp += f"Tu dois faire un cadeau &agrave; {u['receiver_name']}.<br>"
#     resp += f"Tu ne le sais pas mais tu vas recevoir un cadeau de {u['santa_name']}."
#     return resp


import hashlib
import random


SALT = b'1'


USERS = {
    'jules': 'jolleon@gmail.com',
    'guillaume': 'guillaume.lotis@gmail.com',
    'jeanne': 'jeanne.olleon@gmail.com',
    'françois': 'francois@olleon.com',
    'elisa': 'elisa@olleon.com',
    'catherine': 'catherine.lotis@laposte.net',
    'gilles': 'gilles.lotis@laposte.net',
    'emilie': 'erellou@yahoo.fr',
    'pierre': 'pierre@olleon.com',
    'denis': 'denis@olleon.com',
    'marie': 'marie.olleon.dumas@gmail.com',
    'anthony': 'anthofabien@gmail.com',
    'christine': 'chris.gm.63@gmail.com',
}

# for testing
#USERS = { name: f"guillaume.lotis+{name}@gmail.com" for name in USERS }

N = len(USERS)


FAMILIES = {
    'lavault': {'jules', 'jeanne', 'françois', 'elisa'},
    'lotis': {'guillaume', 'catherine', 'emilie', 'gilles', 'anthony'},
    'dumas': {'pierre', 'denis', 'marie', 'christine'},
}


def build_families():
    families = { user: user for user in USERS.keys() }
    for f, members in FAMILIES.items():
        for m in members:
            families[m] = f
    return families

USER_FAMILIES = build_families()

def same_family(user1, user2):
    return USER_FAMILIES[user1] == USER_FAMILIES[user2]


def random_order_users():
    random.seed(12384)
    return sorted(USERS.keys(), key=lambda u: random.random())


def random_order_alternating_families():
    ordered_users = random_order_users()
    #print(ordered_users)
    no_same_family = 0
    i = 0
    while no_same_family < N:
        if same_family(ordered_users[i % N], ordered_users[(i+1) % N]):
            no_same_family = 0
            j = i + 2
            while same_family(ordered_users[(i+1) % N], ordered_users[j % N]):
                j += 1
            ordered_users[(i+1) % N], ordered_users[j % N] = ordered_users[j % N], ordered_users[(i+1) % N]
            print(ordered_users)
        else:
            no_same_family += 1
        i += 1
        if i > N*N:
            raise Exception('impossible to find random order alternating families')
    return ordered_users


SANTAS_ORDER = random_order_alternating_families()


def build_santa_dict():
    santas = {u :{} for u in USERS.keys()}
    for i in range(N):
        santas[SANTAS_ORDER[i]] = {
            'santa': SANTAS_ORDER[(i-1) % N],
            'receiver': SANTAS_ORDER[(i+1) % N],
        }
    return santas

SANTAS = build_santa_dict()


def hash(name):
    m = hashlib.sha256()
    m.update(name.encode('utf-8'))
    m.update(SALT)
    return m.hexdigest()


HASHED_USERS = {
    name: hash(name) for name in USERS.keys()
}

REVERSE_HASH = {
    h: n for n, h in HASHED_USERS.items()
}


def get_hash(u):
    return HASHED_USERS[u]


def get_user(h):
    u = REVERSE_HASH[h]
    santa = SANTAS[u]['santa']
    receiver = SANTAS[u]['receiver']
    return {
        'user': u,
        'santa_name': santa,
        'santa_email': USERS[santa],
        'santa_token': HASHED_USERS[santa],
        'receiver_name': receiver,
        'receiver_email': USERS[receiver],
        'receiver_token': HASHED_USERS[receiver],
    }

# -----------------------------------------------------------------------------
# LOOPING CODE :
# -----------------------------------------------------------------------------
    
import boto3

json_fill = [
    {
        "action": "/default/lamagiedenoel/",
        "title": "Fournis une aide a ton Santa :",
        "name": "toSanta",
        "placeholder": "1. un livre\n2. une cassette VHS\n...\nX. un dessin"
    },
    {
        "action": "/default/lamagiedenoel/",
        "title": "Envoi un email a ton receveur :",
        "name": "toReceiver",
        "placeholder": "Hey, tu ne devineras jamais qui je suis, mais peux-tu s'il te pla&icirc;t me donner des indications plus pr&eacute;cises ?"
    }
]

def indexLooping():
    resp = "<div>Secret Santa Oll&eacute;on !</div>"
    return resp
    
def choose_message_page(token, method):
    u = get_user(token)
    receiver_name = u['receiver_name']
    resp = '<!DOCTYPE html> <html> <head> <meta name="viewport" content="width=device-width, initial-scale=1"> <style> body, html { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100dvh; margin: 0; overflow: hidden } .background-container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; animation: moveGradient 7s linear infinite; background: linear-gradient(45deg, #ffffff, #ff0000); background-size: 400% 400%; } @keyframes moveGradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } } .container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; height: 100%; z-index: 4; } .option { margin: 10px; } .option a { text-decoration: none; background-color: #ff0000; color: white; padding: 10px 20px; border-radius: 5px; font-size: 16px; margin: 10px; display: block; } .option a:hover { background-color: #45a049; } .top, .bottom { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; } .separator { height: 1px; width: 100%; background-color: black; } </style> </head> '
    resp += f'<body> <div class="background-container"></div> <div class="container" style="text-align: center"> <h3>Salut {u["user"]}!</h3> <div class="top option"> <image width="200" height="200" src="https://firebasestorage.googleapis.com/v0/b/licker63-2e940.appspot.com/o/Nouveau%20projet.png?alt=media&token=fae05714-3161-4c9c-bc64-92570f7a1311&_gl=1*1dr5gnb*_ga*NTUyOTM0MTcyLjE2NjgyNjc5MDQ.*_ga_CW55HF8NVT*MTY5ODMzMTkwNi40OC4xLjE2OTgzMzI2NTMuNTMuMC4w" alt="_blank"></image> '
    resp += '<a href="/default/lamagiedenoel/'
    resp += f'{token}/toSanta">Donne des indications a ton Santa</a> </div> <div class="separator"></div> <div class="bottom option"> <a href="/default/lamagiedenoel/'
    resp += f'{token}/toReceiver">'
    resp += f'Envoie un email a ton receveur <strong>({receiver_name})</strong></a> </div> </div> </body> </html>'
    return resp

def write_message_page(token, direction):
    u = get_user(token)
    if direction == "toSanta":
        index = 0
        title = "Fournis une aide a ton Santa :"
    else:
        index = 1
        title = f"Envoi un email a ton receveur ({u['receiver_name']}) :"
    index = 0 if direction == "toSanta" else 1
    resp = """
    <!DOCTYPE html> 
    <html> 
    <head> 
    <meta name="viewport" content="width=device-width, initial-scale=1">"""
    resp += "<style> body, html { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100dvh; margin: 0; overflow: hidden } .background-container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; animation: moveGradient 7s linear infinite; background: linear-gradient(45deg, #ffffff, #ff0000); background-size: 400% 400%; } @keyframes moveGradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } } .container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; height: 100%; z-index: 4; } .top, .bottom { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; } .title { width: 80%; max-width: 400px; font-size: 24px; font-weight: bold; text-align: center; } .big-textarea { width: 80%; max-width: 400px; height: 100px; padding: 15px; border: 2px solid #ccc; border-radius: 10px; font-size: 18px; margin-top: 15px; } .big-textarea::placeholder { color: rgb(189, 189, 189); opacity: 1; } .submit-button { margin-top: 14px; background-color: #ff0000; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; } .submit-button:hover { background-color: #45a049; } </style>"
    resp += """
    </head> 
    <body> 
        <div class="background-container"></div> 
        <div class="container"> 
            <form class="top" action="/default/lamagiedenoel/{token}/{direction}" method="POST">
                <h3>Salut {user}!</h3>
                <div class="title">{title}</div>
                <textarea class="big-textarea" type="text" name="message_body" placeholder="{placeholder}"></textarea>
                <input type="submit" value="Envoyer l email" class="submit-button" onclick="sendPostRequest()">
            </form>
        </div> 
    </body> 
    </html>""".format(
        user=u['user'],
        token=token,
        direction=direction,
        title=title,
        placeholder=json_fill[index]['placeholder']
        )
    
    #resp = """
    #<form action="/default/lamagiedenoel/{token}/{direction}" method="POST">
    #    <textarea type="text" name="message_body" placeholder="{placeholder}"></textarea>
    #    <input type="submit" value="Envoyer l email" class="submit-button" onclick="sendPostRequest()">
    #</form>""".format(
    #    token=token,
    #    direction=direction,
    #    title=json_fill[index]['title']
    #    placeholder=json_fill[index]['placeholder']
    #    )
    return resp


def send_email(body, subject, email):
    try:
        client = boto3.client('ses', region_name='eu-west-3')
        response = client.send_email(
            Destination={
                'ToAddresses': [email],
            },
            Message={
                'Body': {
                    'Html': {
                        'Data': body,
                    },
                },
                'Subject': {
                    'Data': subject,
                },
            },
            Source='secret.santa.olleon@guillaume-lotis.com',
        )
        return True
    except Exception as e:
        print("Error sending email :", email)
        return False


def sendStartMailToEveryone():
    for u, h in HASHED_USERS.items():
        unHashedUser = get_user(h)
        send_email(startMailText(u, h, unHashedUser['receiver_name']), "Secret Santa Olléon", USERS.get(u, 'User not found'))

        
def startMailText(user, token, receiver):
    response = (
        f"<html>Salut <strong style='font-weight: 800;'>{user}</strong>!<br>"
        f"C'est le début du Secret Santa Olléon ! On t'a donné un lien que tu dois conserver précieusement !"
        f"Si tu le perds, on pourra t'en fournir un autre, mais bon, évitons ça ! "
        f"Avec ce lien, tu pourras communiquer secrètement avec la personne à qui tu offres un cadeau (receveur) qui est <strong style='color:red;font-weight: 800;'>{receiver}</strong> "
        f"et la personne qui te donne un cadeau (Santa) qui t'est inconnue. Fais-en bon usage !<br><br>"
        f'<a href="https://7r9qj216hb.execute-api.eu-west-3.amazonaws.com/default/lamagiedenoel/{token}">Lien vers ta page secrète !</a><br><br>'
        f"Note :<br>Si tu envoies des messages (ce qui envoie un e-mail à ton destinataire), tu recevras une copie de cet e-mail pour te confirmer que c'est bien envoyé.<br>"
    )
    return response
    
def make_success_html(success):
    return """<!DOCTYPE html> <html> <head> <meta name="viewport" content="width=device-width, initial-scale=1">
    <style> body, html {{ font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }}
    .background-container {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; animation: moveGradient 7s linear infinite; background: linear-gradient(45deg, #ffffff, #ff0000);
    background-size: 400% 400%; }}
    @keyframes moveGradient {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
    .container {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; height: 100%; z-index: 4; }}
    .top, .bottom {{ flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; }} .title {{ width: 80%; max-width: 400px; font-size: 24px; font-weight: bold; text-align: center; }} </style>
    </head> <body>
    <div class="background-container"></div> <div class="container"> <div class="bottom"> <div class="title">{}</div> </div></div></body></html>""".format(
        "Email envoy&eacute; avec succ&egrave;s" if success else "Erreur lors de l'envoi de l'email")

    

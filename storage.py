from typing import Dict

import peewee
import playhouse.fields

from entities import Vote

db = peewee.SqliteDatabase('votes.db')


class VoteModel(peewee.Model):
    class Meta:
        database = db
    user_id = peewee.IntegerField()
    msg_id = peewee.IntegerField()
    users = playhouse.fields.PickledField()
    text = peewee.TextField()


db.create_tables([VoteModel], safe=True)

UserData = Dict[str, Vote]
data: Dict[str, UserData] = {}


def get_vote_data(user_id, msg_id) -> Vote:
    if user_id in data and msg_id in data[user_id]:
        return data[user_id][msg_id]

    v = VoteModel.filter(user_id=user_id, msg_id=msg_id)
    if v:
        user_data = data.setdefault(user_id, {})
        user_data[msg_id] = Vote(users=v[0].users, text=v[0].text)
        return user_data[msg_id]


def save_vote_data(user_id, msg_id) -> VoteModel:
    d = dict(user_id=user_id, msg_id=msg_id)
    voters = data[user_id][msg_id]
    defaults = dict(d, text=voters.text, users=voters.users)
    vote, created = VoteModel.get_or_create(defaults=defaults, **d)
    vote.users = voters.users
    vote.save()
    return vote


def get_user_data(user_id) -> UserData:
    return data.setdefault(user_id, {})
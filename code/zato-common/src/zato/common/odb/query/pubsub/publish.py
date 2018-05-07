# -*- coding: utf-8 -*-

"""
Copyright (C) 2018, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# gevent
from gevent import sleep

# SQLAlchemy
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

# Zato
from zato.common import PUBSUB
from zato.common.exception import BadRequest
from zato.common.odb.model import PubSubEndpoint, PubSubEndpointEnqueuedMessage, PubSubEndpointTopic, PubSubMessage, PubSubTopic
from zato.common.util.sql import sql_op_with_deadlock_retry

# ################################################################################################################################

MsgInsert = PubSubMessage.__table__.insert
EndpointTopicInsert = PubSubEndpointTopic.__table__.insert
EnqueuedMsgInsert = PubSubEndpointEnqueuedMessage.__table__.insert

MsgTable = PubSubMessage.__table__
TopicTable = PubSubTopic.__table__
EndpointTable = PubSubEndpoint.__table__
EndpointTopicTable = PubSubEndpointTopic.__table__

# ################################################################################################################################

_initialized=PUBSUB.DELIVERY_STATUS.INITIALIZED

# ################################################################################################################################

def _insert_topic_messages(session, msg_list):
    """ A low-level implementation for insert_topic_messages.
    """
    session.execute(MsgInsert().values(msg_list))

# ################################################################################################################################

def insert_topic_messages(session, cid, msg_list):
    """ Publishes messages to a topic, i.e. runs an INSERT that inserts rows, one for each message.
    """
    try:
        return sql_op_with_deadlock_retry(cid, 'insert_topic_messages', _insert_topic_messages, session, msg_list)
    # Catch duplicate MsgId values sent by clients
    except IntegrityError as e:
        if 'pubsb_msg_pubmsg_id_idx' in e.message:
            raise BadRequest(cid, 'Duplicate msg_id:`{}`'.format(e.message))
        else:
            raise

# ################################################################################################################################

def _insert_queue_messages(session, queue_msgs):
    """ A low-level call to enqueue messages.
    """
    session.execute(EnqueuedMsgInsert().values(queue_msgs))

# ################################################################################################################################

def insert_queue_messages(session, cluster_id, subscriptions_by_topic, msg_list, topic_id, now, cid, _initialized=_initialized):
    """ Moves messages to each subscriber's queue, i.e. runs an INSERT that adds relevant references to the topic message.
    Also, updates each message's is_in_sub_queue flag to indicate that it is no longer available for other subscribers.
    """
    queue_msgs = []

    for sub in subscriptions_by_topic:
        for msg in msg_list:

            # Enqueues the message for each subscriber
            queue_msgs.append({
                'creation_time': now,
                'pub_msg_id': msg['pub_msg_id'],
                'endpoint_id': sub.endpoint_id,
                'topic_id': topic_id,
                'sub_key': sub.sub_key,
                'cluster_id': cluster_id,
            })

    # Move the message to endpoint queues
    return sql_op_with_deadlock_retry(cid, 'insert_queue_messages', _insert_queue_messages, session, queue_msgs)

# ################################################################################################################################

"""
Chat Service
Handles Firestore operations for chat history and messages
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from firebase_admin import firestore
import uuid
import json


class ChatService:
    """Service for chat history and message operations"""

    def __init__(self):
        self.db = firestore.client()
        self.chats_collection = 'chats'
        self.messages_subcollection = 'messages'

    # ========================================================================
    # Chat Operations
    # ========================================================================

    def create_chat(
        self,
        project_id: str,
        owner_uid: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new chat session

        Args:
            project_id: Project ID
            owner_uid: User ID
            name: Chat name (auto-generated if not provided)

        Returns:
            Created chat data with ID
        """
        chat_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Auto-generate name if not provided
        if not name:
            # Count existing chats for this project
            existing_chats = self.get_project_chats(project_id, owner_uid)
            chat_number = len(existing_chats) + 1
            name = f"Chat {chat_number}"

        chat_data = {
            'id': chat_id,
            'project_id': project_id,
            'owner_uid': owner_uid,
            'name': name,
            'created_at': now,
            'updated_at': now,
            'message_count': 0,
            'last_message_preview': '',
            'conversation_state': {
                'messages': []
            }
        }

        # Store in Firestore
        self.db.collection(self.chats_collection).document(chat_id).set(chat_data)

        print(f"✅ Created chat: {chat_id} for project: {project_id}")
        return chat_data

    def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get chat by ID

        Args:
            chat_id: Chat ID

        Returns:
            Chat data or None if not found
        """
        doc = self.db.collection(self.chats_collection).document(chat_id).get()

        if not doc.exists:
            return None

        return doc.to_dict()

    def get_project_chats(
        self,
        project_id: str,
        owner_uid: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all chats for a project

        Args:
            project_id: Project ID
            owner_uid: Owner UID for access control
            limit: Maximum number of chats to return

        Returns:
            List of chat data sorted by updated_at (newest first)
        """
        query = (
            self.db.collection(self.chats_collection)
            .where(filter=firestore.FieldFilter('project_id', '==', project_id))
            .where(filter=firestore.FieldFilter('owner_uid', '==', owner_uid))
        )

        chats = [doc.to_dict() for doc in query.stream()]

        # Sort by updated_at in Python (newest first)
        chats.sort(key=lambda x: x.get('updated_at', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)

        # Apply limit
        chats = chats[:limit]

        print(f"📋 Retrieved {len(chats)} chats for project: {project_id}")
        return chats

    def update_chat_name(
        self,
        chat_id: str,
        owner_uid: str,
        new_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update chat name

        Args:
            chat_id: Chat ID
            owner_uid: Owner UID for access control
            new_name: New chat name

        Returns:
            Updated chat data or None if not found/unauthorized
        """
        # Verify ownership
        chat = self.get_chat(chat_id)
        if not chat or chat.get('owner_uid') != owner_uid:
            return None

        updates = {
            'name': new_name,
            'updated_at': datetime.now(timezone.utc)
        }

        doc_ref = self.db.collection(self.chats_collection).document(chat_id)
        doc_ref.update(updates)

        print(f"✅ Updated chat name: {chat_id} → {new_name}")
        return {**chat, **updates}

    def delete_chat(
        self,
        chat_id: str,
        owner_uid: str
    ) -> bool:
        """
        Delete a chat and all its messages

        Args:
            chat_id: Chat ID
            owner_uid: Owner UID for access control

        Returns:
            True if deleted successfully
        """
        # Verify ownership
        chat = self.get_chat(chat_id)
        if not chat or chat.get('owner_uid') != owner_uid:
            return False

        # Delete all messages in subcollection
        messages_ref = (
            self.db.collection(self.chats_collection)
            .document(chat_id)
            .collection(self.messages_subcollection)
        )

        # Delete in batches (Firestore limit: 500 per batch)
        batch = self.db.batch()
        count = 0
        for doc in messages_ref.stream():
            batch.delete(doc.reference)
            count += 1
            if count >= 500:
                batch.commit()
                batch = self.db.batch()
                count = 0

        if count > 0:
            batch.commit()

        # Delete the chat document
        self.db.collection(self.chats_collection).document(chat_id).delete()

        print(f"🗑️ Deleted chat: {chat_id}")
        return True

    def update_conversation_state(
        self,
        chat_id: str,
        messages_array: List[Dict[str, Any]]
    ) -> bool:
        """
        Update the conversation state (agent's self.messages array)

        Args:
            chat_id: Chat ID
            messages_array: Python agent's conversation history

        Returns:
            True if updated successfully
        """
        try:
            doc_ref = self.db.collection(self.chats_collection).document(chat_id)
            doc_ref.update({
                'conversation_state': {
                    'messages': messages_array
                },
                'updated_at': datetime.now(timezone.utc)
            })

            print(f"✅ Updated conversation state for chat: {chat_id} ({len(messages_array)} messages)")
            return True
        except Exception as e:
            print(f"❌ Failed to update conversation state: {e}")
            return False

    # ========================================================================
    # Message Operations
    # ========================================================================

    def save_message(
        self,
        chat_id: str,
        role: str,
        content: str,
        sql_query: Optional[str] = None,
        table_data: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save a message to chat history

        Args:
            chat_id: Chat ID
            role: 'user' or 'assistant'
            content: Message content
            sql_query: SQL query if executed
            table_data: Query results
            metadata: Additional metadata (tokens, model, etc.)

        Returns:
            Saved message data
        """
        message_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        message_data = {
            'id': message_id,
            'chat_id': chat_id,
            'role': role,
            'content': content,
            'sql_query': sql_query or '',
            'table_data': table_data or [],
            'metadata': metadata or {},
            'timestamp': now,
            'created_at': now
        }

        # Save message to subcollection
        messages_ref = (
            self.db.collection(self.chats_collection)
            .document(chat_id)
            .collection(self.messages_subcollection)
        )
        messages_ref.document(message_id).set(message_data)

        # Update chat metadata
        chat_ref = self.db.collection(self.chats_collection).document(chat_id)
        chat_ref.update({
            'message_count': firestore.Increment(1),
            'updated_at': now,
            'last_message_preview': content[:100] if role == 'user' else ''
        })

        print(f"✅ Saved {role} message to chat: {chat_id}")
        return message_data

    def get_chat_messages(
        self,
        chat_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a chat (paginated)

        Args:
            chat_id: Chat ID
            limit: Maximum messages to return
            offset: Number of messages to skip

        Returns:
            List of messages sorted by timestamp (oldest first)
        """
        messages_ref = (
            self.db.collection(self.chats_collection)
            .document(chat_id)
            .collection(self.messages_subcollection)
        )

        # Fetch all messages and sort in Python (Firestore ordering requires index)
        messages = [doc.to_dict() for doc in messages_ref.stream()]

        # Sort by timestamp (oldest first for chat display)
        messages.sort(key=lambda x: x.get('timestamp', datetime.min.replace(tzinfo=timezone.utc)))

        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        paginated = messages[start_idx:end_idx]

        print(f"📋 Retrieved {len(paginated)} messages for chat: {chat_id}")
        return paginated

    def get_all_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a chat (no pagination)

        Args:
            chat_id: Chat ID

        Returns:
            List of all messages sorted by timestamp
        """
        return self.get_chat_messages(chat_id, limit=10000, offset=0)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_chat_with_validation(
        self,
        chat_id: str,
        owner_uid: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get chat with ownership validation

        Args:
            chat_id: Chat ID
            owner_uid: Owner UID for access control

        Returns:
            Chat data or None if not found/unauthorized
        """
        chat = self.get_chat(chat_id)
        if not chat or chat.get('owner_uid') != owner_uid:
            return None
        return chat

    def get_conversation_state(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Get the stored conversation state for an agent

        Args:
            chat_id: Chat ID

        Returns:
            List of conversation messages (agent's self.messages format)
        """
        chat = self.get_chat(chat_id)
        if not chat:
            return []

        return chat.get('conversation_state', {}).get('messages', [])

    def batch_delete_project_chats(
        self,
        project_id: str,
        owner_uid: str
    ) -> int:
        """
        Delete all chats for a project

        Args:
            project_id: Project ID
            owner_uid: Owner UID for access control

        Returns:
            Number of chats deleted
        """
        chats = self.get_project_chats(project_id, owner_uid)
        count = 0

        for chat in chats:
            if self.delete_chat(chat['id'], owner_uid):
                count += 1

        print(f"🗑️ Batch deleted {count} chats for project: {project_id}")
        return count

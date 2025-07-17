from flask import Blueprint, request, jsonify
import asyncio
import base64
import io

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/api/v1/upload', methods=['POST'])
def upload_files():
    """Handle file upload and return expected structure for React frontend"""
    try:
        data = request.json
        contents = data.get('contents', [])
        filenames = data.get('filenames', [])
        
        # Get services from container
        from core.service_container import ServiceContainer
        container = ServiceContainer()
        upload_service = container.get("upload_processor")
        
        # Process files using existing base code
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result_dict = loop.run_until_complete(
            upload_service.process_uploaded_files(contents, filenames)
        )
        loop.close()
        
        # Ensure structure matches what React expects
        response = {
            'upload_results': result_dict.get('upload_results', []),
            'file_preview_components': result_dict.get('file_preview_components', []),
            'file_info_dict': {}
        }
        
        # Process each file's info
        file_info_dict = result_dict.get('file_info_dict', {})
        for filename, info in file_info_dict.items():
            # Get AI column suggestions
            from services.data_enhancer import get_ai_column_suggestions
            df = upload_service.store.get_all_data().get(filename)
            
            ai_suggestions = {}
            if df is not None:
                ai_suggestions = get_ai_column_suggestions(df)
            
            response['file_info_dict'][filename] = {
                'filename': filename,
                'rows': info.get('rows', 0),
                'columns': info.get('columns', 0),
                'ai_suggestions': ai_suggestions,
                'column_names': info.get('column_names', [])
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

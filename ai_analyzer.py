# ai_organizer/ai_analyzer.py
import json
import logging
import os
from .utils import create_default_hierarchy, balance_braces, clean_json_str, logger
try:
    import requests # type: ignore
except ImportError:
    print("requests module not available - this is normal when working in an IDE")
import bpy

class AIAnalyzer:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.response_data = None
        self.progress = 0

    def generate_prompt(self, scene_data):
        """AI 분석을 위한 프롬프트 생성"""
        prompt = f"""
            Analyze the following 3D scene data to determine its context and provide a structured organization plan:

            1. Scene Context Analysis:
               - Identify the overall theme and style (e.g., realistic, stylized, technical).
               - Determine the scene type (e.g., architectural, environment, props, technical, character).
               - Provide a brief description of the scene's purpose and key elements.

            2. Naming and Organization Strategy:
               A. Geometry Data Naming:
                  - Use concise asset-style names with a "GEO_" prefix (e.g., "GEO_Chair", "GEO_Wall").
                  - Ensure names are clear and reflect the geometry's purpose.

               B. Object Naming:
                  - Reflect the object's specific role and location in the scene.
                  - Use context-appropriate terms (e.g., "Main_Entrance", "Decorative_Sword").

               C. Collection Structure:
                  - Propose a hierarchy based on the scene type.
                  - Ensure each object is placed in a relevant collection path (e.g., ["Buildings", "Roofs"]).
                  - Example: An object named "Main_Entrance" should be placed in ["Buildings", "Entrances"].
                  - Use collection paths, not the object names directly as collection names

            Provide your analysis in the following JSON format:
            {{
                "scene_context": {{
                    "type": "scene type (architecture, props, etc.)",
                    "style": "scene style description",
                    "description": "brief scene description"
                }},
                "collection_hierarchy": {{
                    "name": "Root",
                    "children": [
                        {{
                            "name": "Context-appropriate collection name",
                            "description": "Purpose in this scene type",
                            "objects": ["obj1", "obj2"],
                            "children": []
                        }}
                    ]
                }},
                "object_metadata": {{
                    "object_name": {{
                        "new_name": "Context-appropriate detailed name",
                        "category_path": ["Collection", "Subcollection"],
                        "purpose": "Specific role in this scene",
                        "uses_geometry": "corresponding geometry asset name"
                    }}
                }},
                "geometry_metadata": {{
                    "geometry_hash": {{
                        "asset_name": "GEO_ConciseName",
                        "core_purpose": "What this geometry represents",
                        "shared_by": ["object1", "object2"]
                    }}
                }}
            }}

            Start by identifying the scene context, then apply appropriate naming and organization strategies for that specific type of scene.
            
            Scene Data:\n{json.dumps(scene_data, indent=2)}
        """
        return prompt

    def analyze_scene(self, scene_data, context):
        """AI로 씬 분석"""
        try:
            logger.info("Starting AI scene analysis.")
            prompt = self.generate_prompt(scene_data)
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            api_url = f"{self.api_url}?key={self.api_key}"
            session = requests.Session()
            response = session.post(api_url, headers=headers, json=payload)
            self.response_data = response
            
            if response.status_code == 200:
                logger.info("AI analysis API request successful.")
                result = response.json()
                text_content = result['candidates'][0]['content']['parts'][0]['text']
                
                if bpy.context.scene.ai_organizer_save_response:
                    self._save_ai_response(text_content)
                
                try:
                    # JSON 부분 찾기 및 정리
                    json_start = text_content.find('{')
                    json_end = text_content.rfind('}') + 1
                    
                    if json_start != -1 and json_end != 0:
                        json_str = text_content[json_start:json_end]
                        
                        # JSON 문자열 정리 개선
                        json_str = json_str.replace("'", '"')
                        json_str = json_str.replace('\n', '')
                        json_str = ' '.join(json_str.split())
                                                
                        # JSON 구조 정리
                        json_str = clean_json_str(json_str)
                        json_str = balance_braces(json_str)
                        
                        try:
                            logger.debug(f"Final JSON structure: {json_str}")
                            analysis_results = json.loads(json_str)
                            logger.info("AI analysis completed successfully.")
                            return analysis_results
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON parsing error: {e}, JSON String: {json_str}", exc_info=True)
                            raise
                    else:
                        logger.error("No JSON found in response.")
                        raise ValueError("No JSON found in response")
                except Exception as e:
                    logger.error(f"JSON 처리 중 오류 발생: {e}", exc_info=True) 
                    raise

            else:
                logger.error(f"AI analysis API request failed with status code: {response.status_code}, response: {response.text}")
                return create_default_hierarchy()
        except Exception as e:
            logger.error(f"AI analysis error: {e}", exc_info=True)
            return create_default_hierarchy()
        finally:
            from .utils import update_progress
            update_progress(context, 100)
            
    def _save_ai_response(self, response_text):
        """AI 응답 저장"""
        save_path = bpy.context.scene.ai_organizer_response_path
        if not save_path:
            logger.warning("AI 응답 저장 경로가 설정되지 않았습니다. 저장하지 않습니다.")
            return
        
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(response_text)
            logger.info(f"AI 응답이 다음 경로에 저장되었습니다: {save_path}")
        except Exception as e:
             logger.error(f"AI 응답 파일 저장 오류: {e}", exc_info=True)
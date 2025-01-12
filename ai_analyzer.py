import json
import logging
import os
from datetime import datetime
from pathlib import Path
from .utils import create_default_hierarchy, balance_braces, clean_json_str, logger

try:
    import bpy
except ImportError:
    pass
try:
    import requests #type: ignore
except ImportError:
    print("requests module not available - this is normal when IDE testing")

class AIAnalyzer:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.response_data = None

    def generate_prompt(self, scene_data):
        """Generate a comprehensive prompt for scene analysis"""
        prompt = f"""
        You are a professional 3D scene organization expert specializing in optimizing complex scene hierarchies. 
        Your task is to analyze the provided scene data and create an intelligent, context-aware organizational structure.

        TECHNICAL DATA INTERPRETATION:
        1. Vertex/Face Data Structure
           - All geometry data is Base64 encoded
           - Vertex Coordinate System (Blender):
             * X-axis: right(+) / left(-)
             * Y-axis: forward(+) / backward(-)
             * Z-axis: up(+) / down(-) [height]
           - Decoding Process:
             * Base64 decode to binary data
             * Every 12 bytes represent three 32-bit floats (x,y,z)
             * These coordinates reveal exact object positions and shapes
           - Face Indices:
             * Follow vertex positions
             * Define how vertices connect to form faces

        ORGANIZATION REQUIREMENTS:

        1. Data Block Naming Conventions
           - Geometry: GEO_[Type][Variant]
             Examples: GEO_Wall_Standard, GEO_Chair_Office
           - Lights: LIGHT_[Type]_[Purpose]
             Examples: LIGHT_Spot_Key, LIGHT_Area_Fill
           - Cameras: CAM_[Type]_[Specs]
             Examples: CAM_Persp_35mm, CAM_Ortho_Wide

        2. Instance Naming Conventions
           - Objects: [Area]_[Type]_[Purpose]_[##]
             Example: MainHall_Chair_Guest_01
           - Lights: [Area]_Light_[Type]_[Purpose]
             Example: Stage_Light_Spot_Key
           - Cameras: [Area]_Cam_[Purpose]
             Example: MainHall_Cam_Wide

        3. Collection Structure Examples
           Adapt these structures based on scene context:

           Architectural Visualization:
           ```
           Scene Collection
           ├── Sets
           │   ├── Architecture
           │   │   ├── Primary Structure
           │   │   │   ├── Set_Wall_Exterior_North_01 (Using GEO_Wall_Standard)
           │   │   │   ├── Set_Floor_Main_01 (Using GEO_Floor_Marble)
           │   │   │   └── Set_Column_Support_01 (Using GEO_Column_Round)
           │   │   └── Openings
           │   │       ├── Set_Window_Display_Front_01 (Using GEO_Window_Large)
           │   │       └── Set_Door_Entry_Double_01 (Using GEO_Door_Glass)
           │   └── Infrastructure
           │       └── [infrastructure elements...]
           ├── Staging
           │   ├── Primary Elements
           │   │   └── [key visual elements...]
           │   └── Support Elements
           │       └── [supporting elements...]
           └── [other categories as needed...]
           ```

           Medieval Village:
           ```
           Scene Collection
           ├── Sets
           │   ├── Terrain
           │   │   ├── Primary Ground
           │   │   │   ├── Set_Ground_Plaza_Main_01 (Using GEO_Ground_Cobblestone)
           │   │   │   └── Set_Path_Market_01 (Using GEO_Path_Dirt)
           │   │   └── Landscaping
           │   │       └── [terrain features...]
           │   └── Architecture
           │       ├── Main Street
           │       │   ├── Set_House_Merchant_01 (Using GEO_Building_Tudor)
           │       │   └── Set_Shop_Blacksmith_01 (Using GEO_Building_Workshop)
           │       └── [other architectural elements...]
           ├── Staging
           │   ├── Commerce
           │   │   ├── Merchant Goods
           │   │   │   ├── Stage_Cart_Goods_01 (Using GEO_Cart_Heavy)
           │   │   │   └── Stage_Barrel_Wine_01 (Using GEO_Barrel_Oak)
           │   │   └── [other commercial elements...]
           │   └── [other staging categories...]
           └── [other main categories as needed...]
           ```

        REQUIRED JSON RESPONSE FORMAT:
        {{
            "scene_analysis": {{
                "purpose": "primary purpose of the scene",
                "scale": "scene scale and scope",
                "style": "visual style",
                "technical_requirements": ["requirement1", "requirement2"]
            }},
            "collection_hierarchy": {{
                "name": "Scene",
                "type": "root",
                "description": "hierarchy rationale",
                "children": [
                    {{
                        "name": "collection name",
                        "type": "category",
                        "description": "purpose and organization logic",
                        "objects": ["object list"],
                        "children": []
                    }}
                ]
            }},
            "data_metadata": {{
                "geometry": {{
                    "hash_id": {{
                        "name": "GEO_name",
                        "type": "geometry type",
                        "purpose": "geometry purpose"
                    }}
                }},
                "lights": {{
                    "light_id": {{
                        "name": "LIGHT_name",
                        "type": "light type",
                        "purpose": "lighting purpose"
                    }}
                }},
                "cameras": {{
                    "camera_id": {{
                        "name": "CAM_name",
                        "type": "camera type",
                        "purpose": "camera purpose"
                    }}
                }}
            }},
            "object_metadata": {{
                "original_name": {{
                    "new_name": "context appropriate name",
                    "collection_path": ["path", "to", "collection"],
                    "type": "object type",
                    "purpose": "specific role in scene",
                    "data_reference": "corresponding data block name"
                }}
            }}
        }}

        Scene Data for Analysis:\n{json.dumps(scene_data, indent=2)}

        Analyze the scene comprehensively and provide a complete organization plan. 
        The structure should reflect the scene's specific purpose, scale, and technical requirements.
        Consider object relationships and spatial organization when creating the hierarchy.
        Ensure proper interpretation of the coordinate system for accurate spatial analysis.
        """
        return prompt

    def analyze_scene(self, scene_data, context):
        """AI로 씬 분석"""
        try:
            logger.info("Starting AI scene analysis")
            prompt = self.generate_prompt(scene_data)
            
            # API 요청 준비
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            # API 요청
            api_url = f"{self.api_url}?key={self.api_key}"
            session = requests.Session()
            response = session.post(api_url, headers=headers, json=payload)
            
            # 응답 저장 - preferences 가져오기
            preferences = bpy.context.preferences.addons["ai_organizer"].preferences
            if preferences.save_response:
                self._save_ai_response(response, preferences)
            
            if response.status_code == 200:
                logger.info("AI analysis API request successful")
                result = response.json()
                text_content = result['candidates'][0]['content']['parts'][0]['text']
                
                try:
                    json_str = self._extract_json_from_response(text_content)
                    if json_str:
                        analysis_results = self._parse_and_validate_json(json_str)
                        if analysis_results:
                            logger.info("AI analysis completed successfully")
                            return analysis_results
                    
                    logger.error("Failed to extract valid JSON from AI response")
                    return create_default_hierarchy()
                    
                except Exception as e:
                    logger.error(f"JSON processing error: {e}", exc_info=True)
                    return create_default_hierarchy()
            else:
                logger.error(f"AI API request failed: {response.status_code}")
                return create_default_hierarchy()
                
        except Exception as e:
            logger.error(f"AI analysis error: {e}", exc_info=True)
            return create_default_hierarchy()
            
    def _extract_json_from_response(self, text_content):
        """AI 응답에서 JSON 추출 및 정제"""
        try:
            # JSON 시작과 끝 위치 찾기
            json_start = text_content.find('{')
            json_end = text_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = text_content[json_start:json_end]
                
                # JSON 문자열 정제
                json_str = json_str.replace("'", '"')  # 작은따옴표를 큰따옴표로 변경
                json_str = json_str.replace('\n', ' ')  # 줄바꿈 제거
                json_str = ' '.join(json_str.split())  # 중복 공백 제거
                
                # 추가 정제 작업
                json_str = json_str.replace('}, }', '}}')
                json_str = json_str.replace('}, ]', '}}')
                
                # 디버깅을 위한 로깅
                logger.debug(f"Extracted JSON string: {json_str[:100]}...")
                
                return json_str
                
            logger.error("No JSON content found in response")
            return None
            
        except Exception as e:
            logger.error(f"JSON extraction error: {e}", exc_info=True)
            return None

    def _parse_and_validate_json(self, json_str):
        """JSON 파싱 및 유효성 검증"""
        try:
            data = json.loads(json_str)
            
            # 필수 최상위 키 확인
            required_keys = ['scene_analysis', 'collection_hierarchy', 
                           'data_metadata', 'object_metadata']
            if not all(key in data for key in required_keys):
                logger.error("Missing required top-level keys in JSON")
                return None

            # collection_hierarchy 유효성 검사
            if not isinstance(data['collection_hierarchy'], dict):
                logger.error("Invalid collection_hierarchy structure")
                return None

            # 기타 검증 로직 추가 가능...

            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"JSON validation error: {e}", exc_info=True)
            return None

    def _save_ai_response(self, response_data, preferences):
        """Save AI response to file with complete data"""
        try:
            if not preferences.save_response:
                return
                
            # response_path가 문자열인지 확인
            response_path = preferences.response_path
            if not response_path:
                logger.error("Response path not set in preferences")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            response_file = Path(response_path) / f"ai_response_{timestamp}.json"
            response_file.parent.mkdir(parents=True, exist_ok=True)

            # 응답 데이터 준비
            try:
                response_json = response_data.json()
            except Exception as e:
                response_json = {"error": "Failed to parse response as JSON"}
                logger.error(f"Failed to parse response as JSON: {e}")

            save_data = {
                "timestamp": datetime.now().isoformat(),
                "request_info": {
                    "url": self.api_url,
                    "status_code": response_data.status_code,
                    "headers": dict(response_data.headers)
                },
                "response_content": response_json,
                "raw_text": response_data.text
            }

            # JSON 파일로 저장
            with open(response_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"AI response successfully saved to: {response_file}")
            
        except Exception as e:
            logger.error(f"Failed to save AI response: {e}", exc_info=True)

    def _count_collections(self, response_data):
        """Helper method to count collections in the response"""
        try:
            def count_recursive(node):
                count = 1  # Count current node
                children = node.get("children", [])
                for child in children:
                    count += count_recursive(child)
                return count

            hierarchy = response_data.json().get("collection_hierarchy", {})
            return count_recursive(hierarchy) if hierarchy else 0
        except:
            return 0
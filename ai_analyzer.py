import json
import logging
from datetime import datetime
from pathlib import Path
from .utils import create_default_hierarchy, balance_braces, clean_json_str, logger

try:
    import bpy
except ImportError:
    pass

# 비동기 라이브러리 임포트 시도
try:
    import aiohttp
    import asyncio
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    import requests #type: ignore

class AIAnalyzer:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.response_data = None
        self.use_async = ASYNC_AVAILABLE
        
        # 배치 처리 설정 초기화
        preferences = bpy.context.preferences.addons["ai_organizer"].preferences
        self.use_batch = preferences.use_batch_processing
        self.batch_size = preferences.batch_size if self.use_batch else None

    def generate_prompt(self, scene_data, batch=None):
        """프롬프트 생성"""
        base_prompt = f"""
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

        if batch:
            base_prompt += f"""
            
            IMPORTANT - BATCH PROCESSING INSTRUCTION:
            This is part of a larger scene organization task. While you have access to the complete context,
            focus your analysis and naming only on the following elements:
            - Processing Type: {batch['type']}
            - Element Range: {batch['range']['start']} to {batch['range']['end']}
            - Total Elements: {batch['range']['end'] - batch['range']['start']}
            
            Follow the scene analysis, naming conventions, and collection hierarchy from the provided context,
            but provide detailed metadata ONLY for the specified elements in this batch.
            """
        
        return base_prompt

    def analyze_scene(self, scene_data, context):
        """씬 분석 시작"""
        try:
            if self.use_async:
                loop = asyncio.get_event_loop()
                if self.use_batch:
                    analysis_results = loop.run_until_complete(
                        self._analyze_scene_stages(scene_data, context)
                    )
                else:
                    prompt = self.generate_prompt(scene_data)
                    analysis_results = loop.run_until_complete(
                        self._request_analysis_async(prompt)
                    )
                return analysis_results
            else:
                if self.use_batch:
                    return self._analyze_scene_sync(scene_data, context)
                else:
                    prompt = self.generate_prompt(scene_data)
                    return self._request_analysis_sync(prompt)
                    
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                logger.info("Falling back to synchronous processing due to closed event loop")
                if self.use_batch:
                    return self._analyze_scene_sync(scene_data, context)
                else:
                    prompt = self.generate_prompt(scene_data)
                    return self._request_analysis_sync(prompt)
            raise
        except Exception as e:
            logger.error(f"Scene analysis error: {e}")
            return create_default_hierarchy()

    async def _analyze_scene_stages(self, scene_data, context):
        """비동기 단계별 씬 분석"""
        try:
            logger.info("Starting AI scene analysis")
            
            initial_analysis = await self._analyze_scene_structure(scene_data)
            if not initial_analysis:
                return create_default_hierarchy()
            
            if self.use_batch:
                batches = self._prepare_batches(scene_data, initial_analysis)
                batch_results = await self._process_batches_parallel(batches)
                final_results = self._merge_results(initial_analysis, batch_results)
            else:
                final_results = initial_analysis
            
            preferences = bpy.context.preferences.addons["ai_organizer"].preferences
            if preferences.save_response:
                self._save_ai_response(final_results, preferences)
            
            logger.info("AI analysis completed successfully")
            return final_results
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}", exc_info=True)
            return create_default_hierarchy()

    def _analyze_scene_sync(self, scene_data, context):
        """동기 단계별 씬 분석"""
        try:
            logger.info("Starting AI scene analysis (synchronous)")
            
            # 1단계: 전체 씬 분석
            initial_analysis = self._request_analysis_sync(
                self.generate_prompt(scene_data)
            )
            if not initial_analysis:
                return create_default_hierarchy()
            
            # 2단계: 배치 작업 준비
            batches = self._prepare_batches(scene_data, initial_analysis)
            
            # 3단계: 순차적 배치 처리
            batch_results = []
            for batch in batches:
                result = self._request_analysis_sync(
                    self.generate_prompt(batch['data'], batch)
                )
                if result:
                    batch_results.append(result)
            
            # 4단계: 결과 통합
            final_results = self._merge_results(initial_analysis, batch_results)
            
            # 응답 저장
            preferences = bpy.context.preferences.addons["ai_organizer"].preferences
            if preferences.save_response:
                self._save_ai_response(final_results, preferences)
            
            logger.info("AI analysis completed successfully (synchronous)")
            return final_results
            
        except Exception as e:
            logger.error(f"Synchronous AI analysis error: {e}", exc_info=True)
            return create_default_hierarchy()

    async def _analyze_scene_structure(self, scene_data):
        """전체 씬의 맥락과 구조 분석"""
        try:
            prompt = self.generate_prompt(scene_data)
            return await self._request_analysis_async(prompt)
        except Exception as e:
            logger.error(f"Scene structure analysis failed: {e}")
            return None

    def _prepare_batches(self, scene_data, initial_analysis):
        """작업 배치 준비"""
        batches = []
        batch_size = 20  # 배치 크기 설정
        
        # 데이터블록 배치 준비
        geometry_items = list(scene_data.get("geometry_database", {}).items())
        for i in range(0, len(geometry_items), batch_size):
            batch = {
                "type": "geometry",
                "data": {
                    "geometry_database": dict(geometry_items[i:i + batch_size])
                },
                "range": {"start": i, "end": min(i + batch_size, len(geometry_items))},
                "initial_analysis": initial_analysis
            }
            batches.append(batch)
        
        # 오브젝트 배치 준비
        objects = scene_data.get("objects", [])
        for i in range(0, len(objects), batch_size):
            batch = {
                "type": "objects",
                "data": {
                    "objects": objects[i:i + batch_size]
                },
                "range": {"start": i, "end": min(i + batch_size, len(objects))},
                "initial_analysis": initial_analysis
            }
            batches.append(batch)
        
        return batches

    async def _process_batches_parallel(self, batches):
        """배치 병렬 처리"""
        try:
            tasks = []
            for batch in batches:
                prompt = self.generate_prompt(batch['data'], batch)
                tasks.append(self._request_analysis_async(prompt))
            
            return await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return []

    async def _request_analysis_async(self, prompt):
        """비동기 API 요청"""
        try:
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}?key={self.api_key}",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        text_content = result['candidates'][0]['content']['parts'][0]['text']
                        return self._parse_response(text_content)
                    else:
                        logger.error(f"API request failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None

    def _request_analysis_sync(self, prompt):
        """동기 API 요청"""
        try:
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                text_content = result['candidates'][0]['content']['parts'][0]['text']
                return self._parse_response(text_content)
            else:
                logger.error(f"API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None

    def _merge_results(self, initial_analysis, batch_results):
        """분석 결과 통합"""
        merged_results = {
            "scene_analysis": initial_analysis["scene_analysis"],
            "collection_hierarchy": initial_analysis["collection_hierarchy"],
            "data_metadata": {"geometry": {}, "lights": {}, "cameras": {}},
            "object_metadata": {}
        }
        
        for result in batch_results:
            if result and isinstance(result, dict):
                if "data_metadata" in result:
                    for category in ["geometry", "lights", "cameras"]:
                        merged_results["data_metadata"][category].update(
                            result["data_metadata"].get(category, {})
                        )
                
                if "object_metadata" in result:
                    merged_results["object_metadata"].update(result["object_metadata"])
        
        return merged_results

    def _parse_response(self, text_content):
        """AI 응답 파싱"""
        try:
            # JSON 문자열 추출
            json_str = self._extract_json_from_response(text_content)
            if not json_str:
                return None

            # 추출된 JSON 문자열 정제
            cleaned_json = clean_json_str(json_str)
            
            # 정제된 JSON 파싱 및 검증
            return self._parse_and_validate_json(cleaned_json)
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            return None

    def _extract_json_from_response(self, text_content):
        """AI 응답에서 JSON 추출"""
        try:
            json_start = text_content.find('{')
            json_end = text_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = text_content[json_start:json_end]
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
            
            # 필수 키 검증
            required_keys = ['scene_analysis', 'collection_hierarchy', 
                            'data_metadata', 'object_metadata']
            if not all(key in data for key in required_keys):
                logger.error("Missing required top-level keys in JSON")
                return None

            # collection_hierarchy 구조 검증
            if not isinstance(data['collection_hierarchy'], dict):
                logger.error("Invalid collection_hierarchy structure")
                return None

            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"JSON validation error: {e}", exc_info=True)
            return None

    def _save_ai_response(self, response_data, preferences, response_type="response"):
        """Save AI response to file"""
        try:
            if not preferences.save_response:
                return
                
            # response_path가 문자열인지 확인
            response_path = preferences.response_path
            if not response_path:
                logger.error("Response path not set in preferences")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_response_{timestamp}_{response_type}.json"
            response_file = Path(response_path) / filename
            
            save_data = {
                "timestamp": datetime.now().isoformat(),
                "type": response_type,
                "response_content": response_data
            }

            with open(response_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"AI response ({response_type}) saved to: {response_file}")
            
        except Exception as e:
            logger.error(f"Failed to save AI response: {e}", exc_info=True)
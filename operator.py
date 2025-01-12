# ai_organizer/operator.py
import bpy
from .data_collector import SceneDataCollector
from .ai_analyzer import AIAnalyzer
from .scene_applier import SceneApplier
from .utils import logger

class AISceneOrganizerOperator(bpy.types.Operator):
    bl_idname = "object.ai_scene_organizer"
    bl_label = "AI Scene Organizer"
    bl_description = "AI로 씬을 분석하고 정리합니다"
    
    def execute(self, context):
        try:
            logger.info("Starting AI Scene Organization.")
            # 씬 데이터 수집
            collector = SceneDataCollector()
            scene_data = collector.collect_scene_data(context)
            if not scene_data:
                logger.error("Scene data collection failed.")
                self.report({'ERROR'}, "Scene data collection failed.")
                return {'CANCELLED'}
            
            # AI 분석
            analyzer = AIAnalyzer(bpy.context.scene.ai_organizer_api_url, bpy.context.scene.ai_organizer_api_key)
            analysis_results = analyzer.analyze_scene(scene_data, context)
            if not analysis_results:
                logger.error("AI analysis failed.")
                self.report({'ERROR'}, "AI analysis failed.")
                return {'CANCELLED'}
            
            # 결과 적용
            applier = SceneApplier()
            applier.apply_analysis_results(context, analysis_results)

            logger.info("AI Scene Organization completed successfully.")
            return {'FINISHED'}
            
        except Exception as e:
            logger.error(f"AI Scene Organization error: {e}", exc_info=True)
            self.report({'ERROR'}, f"AI Scene Organization error: {e}")
            return {'CANCELLED'}
# ai_organizer/scene_applier.py
import bpy
from .utils import get_geometry_hash, create_collection_hierarchy, logger

class SceneApplier:
    def __init__(self):
        self.progress = 0
        self.total_objects = 0

    def apply_analysis_results(self, context, results):
        """분석 결과를 씬에 적용"""
        try:
            logger.info("Starting application of analysis results.")
            
            objects = list(context.scene.objects)
            self.total_objects = len(objects)
            self.progress = 0
            
            # 지오메트리 데이터 이름 변경
            if "geometry_metadata" in results:
                logger.info("Applying geometry name changes.")
                for i, obj in enumerate(objects):
                    if obj.type == 'MESH' and obj.data:
                        geo_hash = get_geometry_hash(obj.data)
                        if geo_hash in results["geometry_metadata"]:
                            metadata = results["geometry_metadata"][geo_hash]
                            # 간결한 에셋 이름 사용
                            try:
                                obj.data.name = metadata["asset_name"]
                                logger.debug(f"Renamed geometry data '{obj.data.name}' to '{metadata['asset_name']}'")
                            except Exception as e:
                                logger.error(f"Error renaming geometry data '{obj.data.name}': {e}", exc_info=True)
                    self.progress = int(((i + 1) / self.total_objects) * 100) / 3
                    from .utils import update_progress
                    update_progress(context, self.progress)


            # 오브젝트 이름 변경
            if "object_metadata" in results:
                logger.info("Applying object name changes.")
                for i, (obj_name, metadata) in enumerate(results["object_metadata"].items()):
                    obj = context.scene.objects.get(obj_name)
                    if obj and "new_name" in metadata:
                        try:
                            obj.name = metadata["new_name"]
                            logger.debug(f"Renamed object '{obj_name}' to '{metadata['new_name']}'")
                        except Exception as e:
                            logger.error(f"Error renaming object '{obj_name}': {e}", exc_info=True)
                    self.progress = int((((i + 1) / len(results["object_metadata"])) * 100 / 3) + 33.3)
                    from .utils import update_progress
                    update_progress(context, self.progress)

            # 컬렉션 구조 생성 및 오브젝트 이동
            if "collection_hierarchy" in results:
                logger.info("Creating collection hierarchy.")
                root_collection = create_collection_hierarchy(context, results["collection_hierarchy"])
                logger.info("Collection hierarchy created.")
                
                # 오브젝트를 AI가 지정한 컬렉션으로 이동
                for i, (obj_name, metadata) in enumerate(results["object_metadata"].items()):
                    obj = context.scene.objects.get(obj_name)
                    if obj and "category_path" in metadata:
                        target_collection = root_collection
                        
                        
                        for col_name in metadata["category_path"]:
                            sub_collection = target_collection.children.get(col_name)
                            if not sub_collection:
                                sub_collection = bpy.data.collections.new(col_name)
                                target_collection.children.link(sub_collection)
                                logger.debug(f"Created sub-collection '{col_name}' in '{target_collection.name}'")
                            target_collection = sub_collection

                        if obj.name not in target_collection.objects:
                            try:
                                target_collection.objects.link(obj)
                                logger.debug(f"Linked object '{obj.name}' to collection '{target_collection.name}'")
                            except Exception as e:
                                logger.error(f"Error linking object '{obj.name}' to collection '{target_collection.name}': {e}", exc_info=True)
                        
                        for col in obj.users_collection[:]:
                            if col != target_collection and col != context.scene.collection:
                                try:
                                    col.objects.unlink(obj)
                                    logger.debug(f"Unlinked object '{obj.name}' from collection '{col.name}'")
                                except Exception as e:
                                    logger.error(f"Error unlinking object '{obj.name}' from collection '{col.name}': {e}", exc_info=True)
                                    
                    self.progress = int((((i + 1) / len(results["object_metadata"])) * 100 / 3) + 66.6)
                    from .utils import update_progress
                    update_progress(context, self.progress)
                                        
            logger.info("Application of analysis results completed.")

        except Exception as e:
            logger.error(f"Error applying analysis results: {e}", exc_info=True)
            raise
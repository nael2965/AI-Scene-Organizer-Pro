import bpy
from .utils import get_geometry_hash, logger

class SceneApplier:
    def __init__(self):
        self.progress = 0
        self.collection_cache = {}

    def apply_analysis_results(self, context, results):
        """Apply AI analysis results to the scene"""
        try:
            logger.info("Starting to apply analysis results to scene")
            
            # Create new organization structure while preserving Scene Collection
            self._process_collection_hierarchy(context, results["collection_hierarchy"])
            
            # Apply data block names and properties
            if "data_metadata" in results:
                self._apply_data_metadata(context, results["data_metadata"])
            
            # Apply object metadata and organize instances
            if "object_metadata" in results:
                self._apply_object_metadata(context, results["object_metadata"])
                
            logger.info("Successfully applied analysis results")
            
        except Exception as e:
            logger.error(f"Error applying analysis results: {e}", exc_info=True)
            raise

    def _process_collection_hierarchy(self, context, hierarchy_info):
        """Process and create collection hierarchy"""
        try:
            scene_collection = context.scene.collection
            
            # Temporarily move all objects to Scene Collection
            self._secure_objects_to_scene_collection(scene_collection)
            
            # Clean up existing collections
            self._cleanup_existing_collections(scene_collection)
            
            # Create new hierarchy
            if hierarchy_info["name"] == "Scene":
                for child in hierarchy_info.get("children", []):
                    new_collection = self._create_collection(child["name"], scene_collection)
                    self._process_collection_children(child, new_collection)
                    
            logger.info("Collection hierarchy successfully processed")
            
        except Exception as e:
            logger.error(f"Error processing collection hierarchy: {e}", exc_info=True)
            raise

    def _secure_objects_to_scene_collection(self, scene_collection):
        """Ensure all objects are safely linked to Scene Collection"""
        try:
            for obj in bpy.data.objects:
                if obj.name not in scene_collection.objects:
                    scene_collection.objects.link(obj)
                    logger.debug(f"Secured object {obj.name} to Scene Collection")
        except Exception as e:
            logger.error(f"Error securing objects: {e}", exc_info=True)

    def _cleanup_existing_collections(self, scene_collection):
        """Clean up existing collections while preserving Scene Collection"""
        try:
            # Unlink child collections from Scene Collection
            for child in list(scene_collection.children):
                scene_collection.children.unlink(child)
                
            # Remove unused collections
            for collection in bpy.data.collections:
                if collection.users == 0:
                    bpy.data.collections.remove(collection)
                    
            logger.debug("Existing collections cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up collections: {e}", exc_info=True)

    def _create_collection(self, name, parent):
        """Create a new collection with proper naming"""
        try:
            new_collection = bpy.data.collections.new(name)
            parent.children.link(new_collection)
            self.collection_cache[name] = new_collection
            logger.debug(f"Created collection: {name}")
            return new_collection
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}", exc_info=True)
            raise

    def _process_collection_children(self, collection_info, parent_collection):
        """Process collection children and organize objects"""
        try:
            # Process objects assigned to this collection
            if "objects" in collection_info:
                for obj_name in collection_info["objects"]:
                    obj = bpy.data.objects.get(obj_name)
                    if obj:
                        # Unlink from other collections except Scene Collection
                        self._manage_object_collection_links(obj, parent_collection)
                        
            # Process child collections recursively
            if "children" in collection_info:
                for child in collection_info["children"]:
                    child_collection = self._create_collection(child["name"], parent_collection)
                    self._process_collection_children(child, child_collection)
                    
        except Exception as e:
            logger.error(f"Error processing collection children: {e}", exc_info=True)

    def _manage_object_collection_links(self, obj, target_collection):
        """Manage object collection links while maintaining Scene Collection reference"""
        try:
            scene_collection = bpy.context.scene.collection
            
            # 현재 컬렉션 멤버십 확인
            current_collections = set(obj.users_collection)
            
            # 대상 컬렉션이 이미 포함되어 있는지 확인
            if target_collection in current_collections:
                # 이미 올바른 컬렉션에 있다면, Scene Collection에서만 제거
                if scene_collection in current_collections and len(current_collections) > 1:
                    scene_collection.objects.unlink(obj)
                return
            
            # 다른 모든 컬렉션에서 제거 (Scene Collection 포함)
            for col in list(current_collections):
                col.objects.unlink(obj)
            
            # 새로운 대상 컬렉션에 링크
            target_collection.objects.link(obj)
            
            logger.debug(f"Successfully managed collection links for {obj.name}")
            
        except Exception as e:
            logger.error(f"Error managing collection links for {obj.name}: {e}")

    def _apply_data_metadata(self, context, metadata):
        """Apply metadata to data blocks"""
        try:
            # Apply geometry metadata
            if "geometry" in metadata:
                for hash_id, geo_meta in metadata["geometry"].items():
                    self._apply_geometry_metadata(context, hash_id, geo_meta)
                    
            # Apply light metadata
            if "lights" in metadata:
                for light_id, light_meta in metadata["lights"].items():
                    self._apply_light_metadata(context, light_id, light_meta)
                    
            # Apply camera metadata
            if "cameras" in metadata:
                for cam_id, cam_meta in metadata["cameras"].items():
                    self._apply_camera_metadata(context, cam_id, cam_meta)
                    
            logger.info("Successfully applied data metadata")
            
        except Exception as e:
            logger.error(f"Error applying data metadata: {e}", exc_info=True)

    def _apply_geometry_metadata(self, context, hash_id, geo_meta):
        """Apply metadata to geometry data blocks"""
        try:
            for obj in context.scene.objects:
                if obj.type == 'MESH' and obj.data:
                    current_hash = get_geometry_hash(obj.data)
                    if str(current_hash) == str(hash_id):
                        obj.data.name = geo_meta["name"]
                        logger.debug(f"Applied geometry metadata to {obj.data.name}")
        except Exception as e:
            logger.error(f"Error applying geometry metadata: {e}", exc_info=True)

    def _apply_light_metadata(self, context, light_id, light_meta):
        """Apply metadata to light data blocks"""
        try:
            if light_id in bpy.data.lights:
                light = bpy.data.lights[light_id]
                light.name = light_meta["name"]
                logger.debug(f"Applied light metadata to {light.name}")
        except Exception as e:
            logger.error(f"Error applying light metadata: {e}", exc_info=True)

    def _apply_camera_metadata(self, context, cam_id, cam_meta):
        """Apply metadata to camera data blocks"""
        try:
            if cam_id in bpy.data.cameras:
                camera = bpy.data.cameras[cam_id]
                camera.name = cam_meta["name"]
                logger.debug(f"Applied camera metadata to {camera.name}")
        except Exception as e:
            logger.error(f"Error applying camera metadata: {e}", exc_info=True)

    def _apply_object_metadata(self, context, obj_metadata):
        """Apply metadata to scene objects"""
        try:
            for orig_name, obj_meta in obj_metadata.items():
                obj = context.scene.objects.get(orig_name)
                if not obj:
                    continue

                # Rename object
                if "new_name" in obj_meta:
                    obj.name = obj_meta["new_name"]

                # Update collection membership
                if "collection_path" in obj_meta:
                    target_collection = self._find_or_create_collection_path(
                        context.scene.collection,
                        obj_meta["collection_path"]
                    )
                    self._manage_object_collection_links(obj, target_collection)

                logger.debug(f"Applied object metadata to {obj.name}")

        except Exception as e:
            logger.error(f"Error applying object metadata: {e}", exc_info=True)

    def _find_or_create_collection_path(self, parent_collection, collection_path):
        """Find or create a collection path"""
        try:
            current_collection = parent_collection
            
            for col_name in collection_path:
                # Check cache first
                if col_name in self.collection_cache:
                    current_collection = self.collection_cache[col_name]
                    continue

                # Check existing children
                found = False
                for child in current_collection.children:
                    if child.name == col_name:
                        current_collection = child
                        self.collection_cache[col_name] = child
                        found = True
                        break

                # Create new if not found
                if not found:
                    current_collection = self._create_collection(col_name, current_collection)

            return current_collection

        except Exception as e:
            logger.error(f"Error finding/creating collection path: {e}", exc_info=True)
            raise
import re

with open('mde.py', 'r') as f:
    content = f.read()

debug_code = '''
                logger.info(f"📁 Processing file: {filename}")
                
                # Debug: Check what's available
                logger.info(f"Upload service type: {type(self.upload_service)}")
                logger.info(f"Upload service methods: {[m for m in dir(self.upload_service) if not m.startswith('_')]}")
                
                # Use existing base code upload service
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    upload_results, preview_components, file_info = loop.run_until_complete(
                        self.upload_service.process_uploaded_files([contents], [filename])
                    )
                    logger.info(f"✅ Upload processing completed successfully")
                except Exception as inner_e:
                    logger.error(f"💥 Inner processing error: {inner_e}")
                    import traceback
                    logger.error(f"💥 Traceback: {traceback.format_exc()}")
                    raise inner_e
                finally:
                    loop.close()'''

content = re.sub(
    r'logger\.info\(f"📁 Processing file: \{filename\}"\).*?loop\.close\(\)',
    debug_code,
    content,
    flags=re.DOTALL
)

with open('mde.py', 'w') as f:
    f.write(content)

print("✅ Added detailed debug logging")

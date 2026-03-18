            api_url = "https://image-api.photoroom.com/v2/edit"

            # 關鍵參數設定
            params = {
                "background.color": "FFFFFF",                    # 純白背景
                "outputSize": f"{TARGET_WIDTH_PX}x{TARGET_HEIGHT_PX}",  # 目標尺寸
                "padding": "0.08",                               # 全域 padding 8%
                "paddingTop": "0.10",                            # 頭頂留白 10%
                "paddingBottom": "0.05",                         # 底部留白 5%
                "export.format": "png"                           # 輸出格式
            }

            # 使用 multipart/form-data 上傳
            files = {"imageFile": (uploaded_file.name, img_data, uploaded_file.type)}
            response = requests.post(api_url, headers=headers, files=files, data=params)

            if response.status_code == 200:
                final_image = Image.open(io.BytesIO(response.content))

                st.success("🎉 自動裁切成功!符合標準大頭照規格")
                
                # 顯示規格資訊
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("寬度", f"{TARGET_WIDTH_PX}px")
                with col2:
                    st.metric("高度", f"{TARGET_HEIGHT_PX}px")
                with col3:
                    st.metric("解析度", "300 DPI")
                
                st.subheader("✅ 大頭照標準規格 3.5×4.5cm")
                
                # 顯示預覽 (縮小到 478x600 以符合參考圖尺寸)
                preview_image = final_image.resize((478, 600), Image.Resampling.LANCZOS)
                st.image(preview_image, width=478)

                # 提供下載
                final_byte_arr = io.BytesIO()
                final_image.save(final_byte_arr, format='PNG', quality=100, dpi=(300, 300))
                
                st.download_button(
                    label="📥 下載標準大頭照 (300dpi 高品質)",
                    data=final_byte_arr.getvalue(),
                    file_name=f"Taiwan_ID_Photo_{uploaded_file.name.split('.')[0]}.png",
                    mime="image/png"
                )
                
                # 顯示規格說明
                with st.expander("📋 查看規格詳情"):
                    st.write("""
                    **符合台灣居留證規範:**
                    - ✅ 頭部高度: 約佔畫面 70-80%
                    - ✅ 頭頂留白: 10% (約 4-5mm)
                    - ✅ 肩膀完整顯示
                    - ✅ 純白背景 (#FFFFFF)
                    - ✅ 解析度: 300 DPI
                    - ✅ 尺寸: 827×1063px (3.5×4.5cm)
                    """)
                    
            else:
                st.error(f"❌ 自動裁切失敗。錯誤碼: {response.status_code}")
                st.error(f"錯誤訊息: {response.text}")
                
                # 提供除錯資訊
                with st.expander("🔍 除錯資訊"):
                    st.json({
                        "status_code": response.status_code,
                        "response": response.text,
                        "api_url": api_url,
                        "params": params
                    })
        
        except Exception as e:
            st.error(f"❌ 發生未知的錯誤: {str(e)}")
            st.exception(e)

st.markdown("---")
st.markdown("ﾩ 2023 跨國人力文件處理系統 | Powered by PhotoRoom AI")

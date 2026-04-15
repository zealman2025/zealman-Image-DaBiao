@echo off
> 提示词合并.txt (
    for %%f in (B\*.txt) do (
        type "%%f"
        echo(
        echo(
    )
)
echo 合并完成！文件保存在 %cd%\提示词合并.txt

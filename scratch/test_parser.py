import requests

url = "https://shopee.vn/product/145199886/43361044265"
cookie = 'language=vi; ssr-tz=Etc/GMT-7; SPC_F=aXvyY22WoKUhJ59hXt97L39fr0DeMF1e; _gcl_au=1.1.1315070319.1781343379; _QPWSDCXHZQA=6f45c5cd-c09d-4de4-878c-89b10b5a36c2; REC7iLP4Q=0b2a6f55-fd88-4ff9-be9a-bb8d152a4b74; _ga=GA1.1.756108217.1781343380; SPC_CLIENTID=YVh2eVkyMldvS1Vomhciqsrhsdaeyrew; _fbp=fb.1.1781343381467.590815648949197173; _hjSessionUser_868286=eyJpZCI6ImE1MTA1NDJmLTg4ZGEtNTdiNi05NmQ4LTljMzQ0MDM4ZDUxZiIsImNyZWF0ZWQiOjE3ODEzNDMzODE2ODMsImV4aXN0aW5nIjp0cnVlfQ==; SPC_U=1360180176; SPC_R_T_IV=aGM2c2ExT0ZYSEIyMlZnVw==; SPC_R_T_ID=VjYiw2l4jQdgoN/i/qfB8+EcRd7N8TRN1bb2dkfGaE331m6erCYStBvFIVO5x/0L3+U5YAmCP8Wi+xaSQZzEJr2RsYiOdjHEkfvtljIY1NrPtwIWYKMd24CKhXXtku2fjChOaYPwBtZiFPLfyQVDF27kKv+Lhau2ZpEYxHM4xig=; SPC_SC_MAIN_SHOP_SA_UD=0; SPC_STK=uUtOuq0vPBiF1HpmlJ+con1G8iL0R0XgBAnTJVpp2NnKLS7/FQpxal+dAGW/zZ5X721I7L1vYnb49OaTBz4kfBHWZyof++7GAxLK1hZd/KinQDBA05xmM7A6qtTlya2Hr+Li/t3yccE1QPOQcrGSaMq35kwZ0Ia8M0mJBOeMb955SbO3Y7EJIlIkVbkEuO1uKBqiv8u1FqLDjGatjR/xVdQ9UZGKKOyYpIor47Bj1d2VCnE/WUzpiuQgKiLZuCN8jgMvrUs8YXP7xaxr2D6kU2ZzC5l3OjfAF9CJXPml4MXvIM8AJM2is8N7k1bx486YWygIpWstJFqGjqJ4NNcEOyhUt+fdzKEssyS/vrJJjGMg+qLMYGfUQ90LBYgm+8pagOqxRmHeK8SI/e8io7x4XChl/E5eXSWVBRyOlQF4WYeHsslvFq1G4JfXA0NE1Ikt; SC_DFP=gxoHqSmMwNQRLfipJxkfyacyLzgNkeAo; CTOKEN=CvyiYXe4EfG%2FtF6Y9O140A%3D%3D; _gcl_gs=2.1.k1$i1783233122$u20759802; _gcl_aw=GCL.1783233126.Cj0KCQjw3qLSBhDaARIsAFTiVh4ptgKNKmM7LIejlzC_GD3FuYM8Tvkrr4xDJI6YIgQLwnx_nOjwW6caAsiOEALw_wcB; _med=refer; _hjSession_868286=eyJpZCI6IjU1ZGQxYWRkLTdiYjAtNGRjZC04N2YxLWFlNGUzMzZlZGQwOCIsImMiOjE3ODMyMzc5NTM0NjcsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; _sapid=899402401bb02f2a8cc9ce4202a8bd41db2142e434adb4a3412c289a; csrftoken=vonheJTLpdObVH5WTDP6lV65ZWvUoc3X; SPC_IA=1; SPC_CDS_CHAT=f679553d-9bc6-4f22-aae9-37a5136ef820; AC_CERT_D=gqRjZGVrxHeFomtpuDE0MjUxOmNhcHRjaGFfY29va2llX2tleaJrdtEAAaRhbGdv0gAAAGSjZGVrwKJjdMRAAAAADGE52xUo3Wm3iC5rRYtPIg498IF1KHCytnPhbjJaI6YqfVhynmwqpbv6ogr0FzEZ/3RtNpmV6B9rxJ+WP6pjaXBoZXJ0ZXh0xQNRAAAADNx4a7FG8JJQyFOK8CrRFN3n9SNhwjSySxHP6Yb84MWavtWzYe3hDENrlTTyDzBtiBUps5n8hWRBPCRxNYQMeHjUmfXVb8M1mPNd3fTeuIPLxZ4NzN5odbhtgwx4RFcpMe1SGOgeBlIlPIpgYfcmOht+qx/+RluKORuZGq7xqSikX84qffCRlcRThfXu6NYOoyml0JbTYv53NDVFd56Y1ZOxox2jS/cTpW6dr/CYI3I0L71ghJUMxTzBXe/gQ15GyvQCZgRzUjYr7lG711aZ6ZnqZ3XTwJHNmvDnWQGoKv3/4YKs6yXDPBuaaLI3siCmcQXZQsgAjsyMc0JFn5s5MmJCRjgVFXws3frwQvvH7hCnXZnu9+byRQVXZEujuHoB7MXWH4tR4UILkXNTtdOAEBcqsAPVcGX10NuQY8mQYYaOeW/0uFNAzHKlSkVWApFrHheDZROJiPmbKIYjJf9AJCrdWVRnHLFoV7bKSaGGpG+FVvf1YazfLgsRBSaLzknFvB+ZV5fxILlA+9GkCOmNP1UdAQbyNdUzlWjxHn3s1nrGGID+QZfPbNHEoIfHNx9aVhG7bT0vXMLIrPYUbm3nZVxXrnUTRzgB0jGraOV6iHZeaVMOFTxlU58VFs6lCy9FZXXjhKIEaZwFXOeM/5iDlsBLDx+apVpWHBT1pLhn8/MSHsEGnQ+N//IyOegjw8ybMz8lUgA3LiCkNamx7D+O0Mzxr1kpNUAqbvK7KpwJY4Qr9GsAmzNM4K6F2kju87tvNh534mDWO7ESf84anfITBazxeXWVMVL4SbUkP33DJIwibaMUsmVhLmHwTwK7Ji8rwvGHeHt5OmPYb6BL0lmuYo+Ay8RmJWN1cNh2+ADqfSvyoZewc5ddUxG30LrY3XvuA8p0ttNK4qRj4Rx4gXb7DGt//GTrmPnQMQv16dxpAZXmhw+Bau2/we1Vllp3FcwASKGSeD5C1i6PwfFUAd/h3m8XJrt/HbkjhumEDJwhFxmnHgkGugL/WK20ResN4hXPBNBGPC5atSgJxpDsjRU74Xn/9MElpzpA9aFo9BTOXjsq4BiYG3VRVOpGxXAXyKIn9wsgoX63ftzBBUuY7SC/5CHUHcYUqjZY+bF+jCOc; sense_sa_r=s; shopee_webUnique_ccd=sGRVxHMy5mG3Z9i2ltd4Yg%3D%3D%7CTeG%2FrUmFmgoaBV7gv6oqrnd238DcMTPTEHxCIv0cA02ejEqDgRESpanKn5l%2FmRKtwLXniZvpHDn44g%3D%3D%7CvzwmkWxUkv3jIaIp%7C08%7C3; ds=20061d942c9fe352c3c20bf173224239; _ga_4GPP1ZXG63=GS2.1.s1783245564$o12$g1$t1783245959$j60$l1$h83924080'

headers_chrome = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Connection': 'keep-alive',
    'Cookie': cookie
}

r = requests.get(url, headers=headers_chrome, timeout=10)
print(f"Status Code: {r.status_code}")
print(f"Response snippet:\n{r.text[:1500]}")
print("====================================")
print(f"Is redirected: {r.history}")
print(f"Final URL: {r.url}")
print(f"Contains REDO.Lab: {'REDO.Lab' in r.text}")
print(f"Contains application/ld+json: {'application/ld+json' in r.text}")

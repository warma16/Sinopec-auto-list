export const get_endpoint=(isDev:boolean)=>{
    if (isDev) return "localhost:8000"
    return `${window.location.host}`
}
var open1 = 1;
function addupdateform()
{
    if(open1==0){
        document.getElementsByName("updatediv")[0].style.display='none'; 
        open1=1;
    }
    else
    {
        document.getElementsByName("updatediv")[0].style.display='block';
        open1=0;
    }
}

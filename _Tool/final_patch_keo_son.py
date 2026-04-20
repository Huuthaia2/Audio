import os
import re

file_path = r"c:\Users\Windows\Documents\MEGA\Audio\truyencogiaothao\zzzzLoi\tinh-ban-keo-son-0030.txt"

content_chap1 = """Nhấp được một chút thì tôi cũng cứ nằm yên mà ngóay chầm chậm con cặc ở bên trong cái lỗ lồn . Nước nhờn bên trong cứ thế mà nhoen nhoét nước chảy ra thêm thật nhiều .Thấy tôi không còn nhấp nữa thì Linh nói
-Anh à , nhấp mạnh nữa đi anh ..sao mà tự dưng dừng lại thế hả anh ..làm mạnh nữa lên đi nào ..em đang sướng ..sướng không thể nào chịu được nữa rồi đây này ..mạnh lên nữa đi anh
-Nhưng anh thích để như thế này rồi ngóay vào bên trong cơ ..như thế sướng hơn .cái lỗ lồn của em cũng bóp con cặc của anh thật mạnh rồi còn gì nữa .chắc là em cũng sướng điên lên rồi chứ gì
-Không sướng thì sao ..không sướng thì làm sao mà em bảo anh nhấp như vậy cơ chứ .Hay là mệt rồi , nếu mệt thì nghỉ một chút rồi làm tiếp với em cũng được mà , có sao đâu , em nhưng mà cứ để bên trong người em như thế này nhé .Em thích được như thế này lắm
-Ai bảo anh mệt cơ chứ ,chẳng có khái niệm mệt ở đây đâu nhé ,chẳng qua là anh thích được để trong người em như thế này thôi .Nào đã thế anh ngóay tiếp cho em không chịu được nữa đây này
Tôi lại ngóay chầm chậm con cặc của mình bên trong cái lỗ lồn cho Linh không thể nào chịu được nữa .Nước nhờn bên trong cái lỗ lồn cứ như thế mà tuôn ra thật nhiều mà thôi ,một lúc sau thì tôi mới rút chầm chậm con cặc của mình ra khỏi cái lỗ lồn rồi nói
-Nào chổng mông lên đi em , cho anh địt cái kiểu khác nào , chổng mông lên thật cao đấy nhé
Linh thấy tôi đứng dậy như vậy thì khẽ cười lườm mà nói lại
-Chỉ được cái như thế là không ai bằng thôi , trông cái mặt dâm dê thế kia ,chỉ muốn vợ chiều những kiểu tắc oai tắc quái thôi.
Tuy nói như vậy nhưng Linh vẫn chổng mông của mình lên rồi khẽ dạng chân của mình ra .Những giọt nước nhờn vẫn nhỏ giọt từ cái lồn xuống bên dưới .Tôi khẽ đứng dậy , cầm con cặc của mình để đúng cái lỗ lồn mà chầm chậm đút vào thêm một chút nữa
Những cảm giác sung sướng lại hiện ra một cách rõ ràng hơn .Với tư thế như vậy thì cái lỗ lồn bóp con cặc của tôi một cách mạnh hơn nữa .Khẽ ôm lấy cái eo thon nhỏ tôi bắt đầu nhấp chầm chầm
Cặp mông trắng ngần căng tròn khẽ va nhẹ nhàng vào đùi tôi làm cho tôi thích không thể nào tả được .Linh cũng cố gắng mà đẩy mạnh cái mông của mình ra đằng sau để tôi có thể đút thật sâu con cặc vào bên trong .Một lúc sau thì Linh không thể nào chịu được nữa mà rên ầm lên
-Úi .. đã quá..sướng quá ..sướng không thể nào chịu đuợc nữa rồ ianh ơi …sao mà dã thế sướng thế hả trời ..thích thật đấy ,a.a. dễ chịu quá ..sướng quá đi.. ưm ưm ..tê hết cả chỗ đó của em rồi ..mạnh nữa lên đi anh ..em sướng
Tôi càng nhấp mạnh hơn thì nước nhờn của Linh cũng chảy ra thêm .Một lúc sau thì tôi và Linh cũng không thể nào chịu đuợc Tôi ấn mạnh cái con cặc của mình thật sâu vào bên trong cái lỗ lồn rồi phóng ầm tinh trùng vào bên trong
Miết mạnh lấy cái eo của Linh tôi nói
-Ui dễ chịu quá ..sướng quá đi mất thôi …híc híc ..sao mà không thể nào chịu được nữa rồi đây này .a.a dễ chịu quá … anh ra đầy vào trong người em rồi đó Linh ơi..ui ui sướng thật

-Thì em cũng sướng không thể nào chịu dược nữa rồi mà anh ..cho thật nhiều vào bên trong người em đi nào ..em thích lắm ..mà em cũng ra rồi đây này .thích quá đi mất thôi ..ui đã
Cùng lúc đó thì nước nhờn bên trong cái lỗ lồn cũng cứ thế mà phun ra thật nhiều hòa cùng với tinh trùng của tôi thành dòng mà chảy xuống dưới cái mặt ghế .Tối cứ để con cặc của mình bên trong cái lỗ lồn một lúc lâu thì mới rút con cặc của mình ra
Tinh trùng vì thế mà chảy ra thật nhiều .Linh ngồi xuống tấy tay xoa chầm chậm cái khe lồn cho nước nhờn cùng với tinh trùng nhoen nhoét hết cả ra , miệng mỉm cười mà nói
-Cái cảm giác buồn buồn thích thật anh ạ .Thảo nào mà người ta bảo làm chuyện này sẽ cảm thấy thỏai mái giải tỏa căng thẳng hơn
Tôi không nói mà chỉ ngồi xuống rồi mút chầm chậm lấy cái núm vú nhỏ tí xíu của Linh .Một lúc sau thì con cặc của tôi cũng cứng lại rồi .Tôi khẽ bảo Linh
-Nào bây giờ thì em ngồi tiếp lên con cặc của anh nhé được không , anh lại thích cái cảm giác lúc nãy rồi dấy.
Linh không nói gì mà dạng chân của mình ra .Cầm con cặc để đúng cái lỗ lồn ấn vào rồi chầm chậm mà ngồi xuống .Con cặc của tôi một lần nữa lại chui ngập vào bên trong cái lỗ lồn.
Linh bắt đầu nhún chầm chậm để cho con cặc trượt dọc theo cái lỗ lồn .Lần này thì nước nhờn của Linh cũng không còn chảy ra nhiều nữa .Một lúc sau thì Linh khẽ ngồi luôn dậy cho con cặc của tôi trượt ra rồi quay lại mà nói
-Em thấy hơi rát rát , thôi chúng ta dừng lại ở đây nhé được không anh , em cũng cảm thấy hơi mệt rồi làm từ chiều đến giờ
-Được thôi , nếu mà em thấy mệt thì chúng ta nghỉ cũng được đâu có sao đâu .Miễn là em thấy thỏai mái là được
Linh khẽ gật đầu rồi chúng tôi đi vào bên trong nhà tắm mà rửa hai chỗ của mình rồi lên giường đi ngủ .Công nhận làm chuyện đó xong thì cũng buồn ngủ không thể nào chịu dược nữa. Chúng tôi đi ngủ nhưng cũng không quên để chuông đồng hồ mai dậy đi học
Chẳng bao lâu thì trời cũng sáng .Hai chúng tôi dậy nhưng vẫn thấy hơi mệt . Ăn sáng xong thì chúng tôi thấy tỉnh hẳn . Đi trên đường thì Linh khẽ thủ thỉ vào tai tôi
-Anh à ,em vẫn thấy hơi ran rát cái chỗ đấy anh ạ .Hay anh em mình làm hơi quá hả anh
-Cũng làm gì mà hơi quá đâu , bình thường thôi mà , chắc là chưa quen thôi .Nhiều khi anh ra chợ , nghe mấy bà ấy nói , phục vụ chồng cả đêm mà sáng cũng chỉ có hơi mệt một chút thôi mà.
-Ùh có lẽ vậy , may mà hôm qua em mua thuốc để dành rồi đấy .Tối mịt như hôm qua không uống là hôm nay coi như toi
Tôi khẽ cười trước câu nói của Linh mà nói lại
-Toi cái gì mà toi cơ chứ , cùng lắm là em có một dứa và có một dứa thì là cuới , có thế mà cũng toi , chẳng có gì là toi cả đâu
Cái đùa nhau một lúc thì tôi cùng với Linh cũng đã đến trường rồi .Chúng tôi đi lên lớp thì cũng thấy Nam và Hội đi lên , thấy hai chúng tôi như vậy thì Hội lại giở giọng trêu
-Trông anh chị đẹp dôi ghê cơ , nhìn cứ như là vợ chồng sắp cưới đến nơi rồi đấy
Lần này thì tôi không để cho Linh đối đáp nữa mà khẽ quay lại nói với Hội luôn
-Sao hả , sắp cưới thật chứ đùa à , không tin à , hay là bà cùng cưới với tụi tôi đi .Như thế có khi lại hay đấy nhỉ .Có con biết đâu tôi với bà lại là thông gia của nhau cũng lên đấy chứ
Tôi nói như vậy thì Hội cười thật tuơi rồi nói lại
-Đúng là ý kiến của ông chuẩn không cần chỉnh . Được đấy , ra trường cưới luôn nhỉ !
Hội nói như vậy thì Nam dỏ mặt lên , vì trêu chúng tôi được nhưng Nam lại rất sợ chúng tôi trêu lại.

Chúng tôi vào lớp thì cô giáo chưa vào .Ngồi ngay ngắn vác sách vở ra ôn lại một chút rồi quay ra tán phét với mấy đứa bạn .Linh thì vẫn ít nói như mọi ngày , chứ không lắm mồm khi đi cùng với tôi
Tiết học đầu tiên cũng trôi qua .Ra chơi tôi ra hành lanh đứng ngắm mấy bạn lớp bên cạnh thì Nam ra hỏi mà nói
-Sao dạo này thấy đi cùng Linh có vẻ thắm thiết thế nhỉ , không còn thấy đi chung với tụi này nữa
-Ơ tạo điều kiện cho ông bà ở bên nhau còn kêu ca cái lỗi gì cơ chứ .Thế muốn tụi tôi đi làm kì đà cản mũi à
-Không phải như vậy , mà thấy hơi kì kì thôi , à mà này thế còn ông với Linh thế nào rồi , yêu nhau thật rồi à. -Không những yêu nhau mà còn cưới nhau nữa .Sắp có con với nhau rồi còn gì nữa .Này đừng có mà bô bô cái miệng ra đấy nghe chưa .Làm chuyện đó với Linh nhiều lần rồi , chúng tôi định ra trường xong thì cưới mà .Thế sao đã làm chuyện đó với Hội chưa
-Hỏi kì lạ nhỉ , đi với nhau như thế không làm chuyện đó mới là lạ đó .Mà công nhận trông Hội như vậy mà lúc lên giường thì dâm không thể nào chịu được , còn Linh trông hiền thế chắc là ông bắt nạt chứ gì
-Ông nhầm hàng to rồi .Linh mà hiền , trông tẩm ngẩm tầm ngầm thể thôi nhé .Lên giường thì cũng không khác gì đại mà nữa đâu .Thế mới gọi là đại dâm tặc chứ.
"""

content_chap2 = """Tôi về nhà ăn cơm tắm rửa một chút rồi leo lên giường đi ngủ , nhưng cũng không quên mà dọn dẹp phòng của minh cho nó bớt bừa bộn đi một chút.
Buổi chiều thì cũng đã đến .Tôi phóng xe đến nhà Linh đứng đợi thì Linh khẽ đi xuống với một bộ quần áo khá là thoáng mát. Trông không khác gì hôm qua cả .Tôi mỉm cười đưa cho Linh cái kem ốc quế rồi nói
-Ăn đi Linh , Long mua cho Linh đấy
Thấy tôi đưa kem như vậy thì Linh cũng mỉm cười ,vì Linh rất thích ăn kem .Bóc cái kem mút nhẹ một cái Linh bảo
-Không ngờ Long như vậy mà cũng tâm lý ra phết đấy nhỉ, biết mua kem cho Linh nữa đấy
-Phải chiều chứ , vợ mình chứ có phải ai đâu mà không chiều được cơ chứ , yên tâm , như thế này rồi lấy về còn chiều hơn nữa cơ
Tôi nói như vậy thì Linh cũng vênh mặt của mình lên mà nói
-Chẳng biết là có thật như vậy không hay lấy về rồi chẳng khác gì ô xin cao cấp, suốt ngày uýnh đấy nhỉ
-Ơ đã nói thật mà không tin , Linh như thế này thì làm sao mà có thể bắt nạt được chứ .Linh không bắt nạt Long thì thôi , nhỉ ! Mà cứ nhầm mãi , vợ chứ nhỉ.
Tôi nói vợ thì Linh cấu mạnh vào lưng tôi một cái làm cho tôi đau điếng . Nhưng tôi đoán chắc là Linh cũng thích tôi .Về đến nhà thì tôi mở cửa rồi bảo Linh lên phòng.Thật ra tôi bảo vậy thôi chứ Linh cũng chẳng còn lạ gì phòng của tôi nữa .
Linh thấy gọn gàng như vậy thì khẽ mỉm cười mà nói
-Hôm nay gọn gàng thế nhỉ , kiểu này tí nữa không về được rồi , trời mưa chắc là to lắm đây
Biết Linh nói kháy tôi nhưng tôi vẫn mỉm cười mà nói lại
-Dọn trước để vợ đỡ phải dọn còn gì nữa , thế mà cũng nói được , yên tâm đi , trời không mưa đâu
Tôi nói xong thì đến mở cửa sổ ra cho nó thoáng một chút .Linh khẽ đến cái bàn học của tôi mà lấy quyển sách văn ra .Tôi mở cửa xong thì đứng mà nhìn Linh .Mái tóc mượt mà khẽ buông nhẹ xuống bờ vai trông xin vô cùng , cái eo thon nhỏ càng tôn thêm cái dáng của Linh lên .
Linh chống tay vào bàn lên cái áo khẽ bị kéo lên phía trên một chút .làn da trắng mịn ở eo lộ ra trông ngon lành vô cùng .Tôi không thể nào chịu được nữa , khẽ tiến lại gần mà ôm chầm chậm lấy Linh vào trong vòng tay của mình
Vẫn giữ thái độ bình tĩnh ,Linh nắm nhẹ nhàng lấy bàn tay của tôi mà nói
-Thôi nào bỏ Linh ra đi Long, nhỡ người nhà Long nhìn thấy thì chết đấy
-Làm gì có ai mà chết cơ chứ , đi hết rồi còn đâu , nhà Long thì đến tối mới có người ở nhà cơ , yên tâm đi , cho anh ôm em một chút nào .Anh yêu em quá đấy Linh ơi
Tôi đổi giọng xưng hô rồi siết chặt vòng tay của mình thêm một chút nữa .Lần này thì Linh không còn muốn tôi bỏ tay ra nữa .Hương thơm nhẹ nhàng của Linh toả ra làm cho tôi thích vô cùng , đây có lẽ hương thơm đầu tiên của một người con gái mà tôi có thể cảm nhận được
Khẽ hôn nhẹ nhàng lên mái tóc của Linh rồi tôi xoa chầm chậm lấy cái bụng thon nhỏ của Linh .Thân hình của Linh cũng dần dần mà ấm lên trước những hành động xoa nhẹ nhàng của tôi .Tôi có xem một số truyện và phim thấy trong hoàn cảnh này thì lên tiến tới tiếp

Khẽ xoay chầm chậm Linh quay về tôi rồi tôi hôn chầm chậm lên đôi môi đỏ mọng ngọt ngào .Không ngờ Linh cũng khẽ ôm nhẹ lấy tôi rồi hôn chầm chậm .Hai bờ môi của tôi dần dần dính vào nhau .
Hơi thở ấm nóng hoà cùng với nước miếng chảy ra quện lại với nhau làm cho tôi thích vô cùng .Tôi càng ôm chặt Linh vào vòng tay của mình hơn nữa . Đưa chầm chậm đầu lưỡi của mình ra để đưa vào trong miệng của Linh thì Linh cũng đưa ra để tôi mút chầm chậm ,cảm giác tê tê buồn buồn của cái đầu lưỡi làm cho tôi thích hơn nữa Hôn Linh như vậy thì hai bàn tay tôi bên dưới cũng không thể nào chịu được, luồn vào bên trong cái áo của Linh mà xoa chầm chậm lấy tấm lưng ong mềm mại .Làn da mịn màng nhưng cũng dần ấm lên khi được bàn tay tôi xoa nhẹ nhẹ
Chẳng mấy chốc thì bày tay tôi đã chạm vào cái áo lót của Linh , tôi đánh liều cởi luôn cái khuy ra thì Linh cũng chẳng còn phản ứng gì nữa .Tôi đoán chắc là Linh đã cho tôi làm rồi lên tôi bế luôn Linh ra giường mà đặt Linh nằm xuống
Vẫn mút chặt cái đôi môi đỏ mọng nhưng tôi cũng cởi chầm chậm cái cúc áo của Linh ra .Vuốt chầm chậm từng đầu ngón tay của mình lên phía trên , chỉ một chút thôi là tôi đã chạm vào hai bầu vú của Linh rồi
Hai bầu vú của Linh cũng không to lắm nhưng được cái áo lót nâng nhẹ lên trông ngon lành không thể nào tả được, khẽ xoa chầm chậm tay của mình vào hai bầu vú đó , thì tôi cũng cảm nhận được sự mềm mại .Linh chắc cũng sướng lắm lên khẽ ưỡn người của mình lên để tôi có thể xoa một chút dễ dàng hơn Do đằng sau thì đã cởi cái khuy áo ra rồi lên tôi cũng khẽ kéo luôn lên mà bóp hai cái bầu vu cho dẽ dàng .Hai núm vú bé tí xíu lộ ra làm cho tôi thích vô cùng .Càng soa càng bóp thì cái bầu vú của Linh càng cứng hơn nữa .
Tôi không thể nào chịu được nữa úp cả bàn tay của mình vào đúng cái bầu vú mà bóp thật mạnh Hơi thở của Linh dần dần trở lên gấp gáp hơn nữa .Một lúc sau thì tôi khẽ dời đôi môi của Linh ra nhưng vẫn bóp chầm chậm lấy cái bầu vú
Thấy tôi làm như vậy thì Linh cũng lườm tôi mà nói
-Chỉ được cái như thế này là không ai bằng thôi .Nhìn cái mặt sao mà đểu thế không biết nữa .Mình biết ngay mà , bảo mình sang kèm chỉ thế này thôi
-Kèm như thế này thì cũng là kèm rồi còn gì nữa , không thấy à , hai vợ chồng mình kèm nhau sát thế này còn gì .Hơn nữa cho chồng sờ một chút có chết ai đâu nào Nói xong như vậy thì tôi vê vê nhẹ nhàng cái núm vú của Linh rồi tiếp tục cúi xuống mà hôn nhẹ lên bờ môi mềm mại rồi đến cái cổ tron dài trắng ngần.Linh khẽ nhắm mắt mình lại , hơi nghển cổ lên một chút để tận hưởng cái cảm giác sung sướng đó
Bóp bầu vú một lúc khá là lâu thì tôi khẽ đưa chầm chậm tay của mình xuống bên dưới mà cởi nhẹ nhàng cái cúc quần của Linh ra . đến đây thì Linh đưa tay xuống nắm lấy tay tôi mà nói
-Đừng thế mà anh , như thế này là đã đi hơi quá giới hạn rồi đấy .Bỏ tay ra đi
-Làm sao mà phải bỏ cơ chứ , vợ chồng thì còn có gì mà ngại với nhau nữa đâu nào .Cho chồng sờ một chút đi vợ ,chồng sắp không thể nào chịu nổi được nữa rồi đây này , mà yên tâm đi nhà chồng có ai đâu mà sợ cơ chứ

Nói xong thì tôi lại đưa tiếp xuống mà cởi chầm chậm cái khoá quần của Linh ra .Vẫn nắm lấy tay tôi nhưng không còn cương quyết như trước nữa , chính vì như vậy mà tôi có thể cởi được cái khoá quần của Linh ra Mới cởi cái khoá thôi mà tôi đã thấy người của Linh ấm hơn trước rồi .Do nằm như thế này thì cũng khó tụt cái quần xuống bên dưới .Tôi úp luôn bàn tay của mình vào đúng cái đũng quần mà day nhè nhẹ .Cảm giác mềm mại của nó thích vô cùng
Chẳng bau lâu sau thì thân hình của Linh cũng căng cứng hết cả lên .Linh cũng khẽ dạng chân của mình ra đôi chút để tôi có thể xoa một cách dễ dàng hơn nữa.Càng ấn bàn tay của tôi vào đúng cái đũng quần thì Linh có phần hơi ưỡn người mình lên một chút
Tôi đoán chắc là Linh cũng đã sướng không thể nào chịu được rồi lên khẽ kéo chầm chậm cái khoá quần xuống bên dưới đồng thời cũng tụt nhẹ nhàng cái quần ra .Cái quần lót đen khẽ hiện loáng thoáng trước mắt tôi
Tôi đưa nhẹ bàn tay của mình mà vuốt chầm chậm xuống bên dưới thì Linh khẽ ôm ghì lấy tôi mà thở hổn hển ra Tôi đoán Linh sướng không thể nào chịu được nữa rồi lên khẽ ngồi dậy, khẽ tụt cái quần của Linh xuống .Linh thấy tôi tụt thì cũng khẽ ưỡn mông của mình lên để tôi có thể tụt một cách dễ dàng hơn .Chẳng mấy chốc thì cái quần lót đã hiện ra trước mắt tôi
Mu lồn của Linh cũng nhô lên khá là cao .Cái đũng quần lót cũng đã ôm sát vào cái mu lồn rồi .Tôi nhìn như vậy thì không thể nào kim dược lòng mình , khẽ úp chầm chậm tay lên đúng cái đũng quần đó mà xoa nhè nhẹ
Một chút nước nhờn bên trong cái lỗ lồn đã chầm chậm mà chảy ra làm ướt cái đũng quần.Tôi không nghĩ Linh lại lầ một cô gái khá là thoải mái đến như vậy .Tôi ấn mạnh tay của mình vào thêm một chút nữa thì Linh càng ưỡn người của mình lên
Tôi thấy trong phim cũng có cảnh hôn chỗ đấy rồi , nhưng chưa biết thế nào lên tôi cũng khẽ cúi xuống mà hôn chầm chậm lên cái bụng rồi đến cái bẹn trắng ngần của Linh .Lần này thì Linh đờ luôn ra rồi mà không còn biết cái gì nữa Mùi nước hoa nhẹ nhàng đưa từ cái quần lót vào mũi tôi cũng làm cho tôi thích hơn hữa .Tôi đánh bạo hôn đúng vào chỗ cái đũng quần , nơi mà đã ướt ướt vì nước nhờn chảy ra thì Linh dạng chận của mình ra thật to như muốn tôi hôn hẳn vào chỗ đó
Khao khát muốn nhìn cái lồn của Linh lắm rồi lên tôi khẽ tụt chầm chậm cái quần lót của Linh xuống một cách từ tốn .Những sợi lông đen nhánh ở cái mu lồn đã chầm chậm mà hiện ra trước mắt tôi .Lông của Linh cũng tuơng đối là mượt mà.
Đầu những sợi lông cũng xoăn lại trông khêu gợi vô cùng .Tôi tụt xuống bên dưới thêm một chút nữa thì cái khe lồn của Linh cũng chầm chậm mà hiện ra.
Khe lồn của Linh khẽ hồng hồng và có một chút nước nhờn chảy ra rồi lên trông ngon lành đến khó tả .Tôi khẽ đưa nhẹ đầu ngón tay của mình vào đúng chỗ đó mà gãi thì những giọt nước nhờn bên trong cái lỗ lồn tiếp tục mà chảy ra nữa Bóp chầm chậm lấy hai cái đùi trắng ngần của Linh thì Linh cũng khẽ run cả người lên vì sướng .Lần này thì tôi cúi xuống hôn nhẹ nhẹ lên đám lông đen mượt đó xem cảm giác như thế nào .Những sợi lông cọ nhẹ vào mũi tôi khiến tôi hơi nhột nhạt một chút nhưng cũng thấy thích vô cùng .Hôn ở phía trên một chút thì tôi khẽ bảo Linh
-Em à , cho anh hôn xuống phía dưới một chút nhé ,xem như thế nào .Công nhận là chỗ ấy của em đẹp thật đấy .Nhìn thích quá đi mất thôi
"""

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Tạo Block Chương 1 & 2 hoàn chỉnh
new_header = "==============================\n TITLE: Tình Bạn Keo Sơn\n==============================\n\n"
chap1_block = "==================== Chương 1 ====================\n\n" + content_chap1 + "\n\n"
chap2_block = "==================== Chương 2 ====================\n\n" + content_chap2 + "\n\n"

# 2. Xóa các tàn dư chương 1 cũ (nếu có) và ghép nối
# Tìm vị trí Chương 3
match_chap3 = re.search(r"==================== Chương 3 ====================", text)
if match_chap3:
    rest_of_file = text[match_chap3.start():]
    full_text = new_header + chap1_block + chap2_block + rest_of_file
else:
    full_text = text # Fallback nếu không thấy Chương 3 (ít khả năng)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(full_text)

print("Final Fix Done: Re-constructed Chapter 1, 2 and merged with the rest.")
